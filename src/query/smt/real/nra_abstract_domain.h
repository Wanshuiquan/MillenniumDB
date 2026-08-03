#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <numeric>
#include <string>
#include "z3++.h"
namespace SMT::Real {
struct NRAAbstractValue { uint32_t magnitude = 1; uint32_t precision = 1; bool infinite_precision = false; };
class NRAAbstractDomain {
public:
 static NRAAbstractValue infer(const z3::expr& e) {
  if(e.is_bool()) return boolean(e); if(e.is_numeral()) return constant(e); if(e.is_const()) return {1024,53,false};
  const auto k=e.decl().decl_kind(); if(k==Z3_OP_UMINUS||k==Z3_OP_TO_REAL)return infer(e.arg(0)); if(k==Z3_OP_ITE)return join(infer(e.arg(1)),infer(e.arg(2)));
  auto r=infer(e.arg(0)); for(unsigned i=1;i<e.num_args();++i){auto x=infer(e.arg(i));if(k==Z3_OP_ADD||k==Z3_OP_SUB)r=add(r,x);else if(k==Z3_OP_MUL||k==Z3_OP_POWER||k==Z3_OP_DIV)r=multiply(r,x);else r=join(r,x);} return r;
 }
 static bool fits_binary64(const NRAAbstractValue& v) { return !v.infinite_precision&&v.magnitude<=1024&&v.precision<=53; }
private:
 static uint32_t bit_width_u64(uint64_t value) {
  if (value == 0) return 0;
  uint32_t width = 0;
  while (value != 0) {
   ++width;
   value >>= 1;
  }
  return width;
 }
 static uint32_t trailing_zero_count_u64(uint64_t value) {
  if (value == 0) return 64;
  uint32_t count = 0;
  while ((value & 1U) == 0U) {
   ++count;
   value >>= 1;
  }
  return count;
 }
 static NRAAbstractValue join(NRAAbstractValue a,NRAAbstractValue b){return {std::max(a.magnitude,b.magnitude),std::max(a.precision,b.precision),a.infinite_precision||b.infinite_precision};}
 static NRAAbstractValue add(NRAAbstractValue a,NRAAbstractValue b){auto r=join(a,b);++r.magnitude;++r.precision;return r;}
 static NRAAbstractValue multiply(NRAAbstractValue a,NRAAbstractValue b){return {a.magnitude+b.magnitude,a.precision+b.precision,a.infinite_precision||b.infinite_precision};}
 // Fig. 5(b)'s implementation-level under-approximation for division.
 static NRAAbstractValue divide(NRAAbstractValue a,NRAAbstractValue b){return {a.magnitude+b.magnitude,a.precision+b.precision,a.infinite_precision||b.infinite_precision};}
 static NRAAbstractValue boolean(const z3::expr& e){NRAAbstractValue r{};for(unsigned i=0;i<e.num_args();++i)r=join(r,infer(e.arg(i)));return r;}
 static NRAAbstractValue constant(const z3::expr& e){
  int64_t num = 0;
  int64_t den = 1;
  if (Z3_get_numeral_rational_int64(e.ctx(), e, &num, &den)) {
   if (den < 0) {
    num = -num;
    den = -den;
   }
   const uint64_t abs_num = num == std::numeric_limits<int64_t>::min() ? (uint64_t{1} << 63) : static_cast<uint64_t>(std::llabs(num));
   const uint64_t abs_den = static_cast<uint64_t>(den);
   const uint64_t gcd = std::gcd(abs_num, abs_den);
   uint64_t reduced_num = gcd == 0 ? abs_num : abs_num / gcd;
   uint64_t reduced_den = gcd == 0 ? abs_den : abs_den / gcd;
   while (reduced_den > 1 && (reduced_den % 2) == 0) {
    reduced_den /= 2;
   }
   if (reduced_num == 0) {
    return {1,1,false};
   }
   const uint32_t magnitude = bit_width_u64(reduced_num);
   const uint32_t trailing = trailing_zero_count_u64(reduced_num);
   const uint64_t odd_num = reduced_num >> trailing;
   const uint32_t precision = bit_width_u64(odd_num);
   return {magnitude,std::max(1u,precision),reduced_den != 1};
  }
  double d = 0.0;
  if (e.is_numeral(d)) {
   if (d == 0.0) return {1,1,false};
   const auto magnitude = static_cast<uint32_t>(std::max(1.0, std::ceil(std::log2(std::abs(d))) + 1.0));
   return {magnitude,53,false};
  }
  return {1024,54,true};
 }
};
} // namespace SMT::Real
