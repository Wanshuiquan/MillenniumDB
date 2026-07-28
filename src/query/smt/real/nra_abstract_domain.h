#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
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
 static NRAAbstractValue join(NRAAbstractValue a,NRAAbstractValue b){return {std::max(a.magnitude,b.magnitude),std::max(a.precision,b.precision),a.infinite_precision||b.infinite_precision};}
 static NRAAbstractValue add(NRAAbstractValue a,NRAAbstractValue b){auto r=join(a,b);++r.magnitude;return r;}
 // Fig. 5(b)'s implementation-level under-approximation for division.
 static NRAAbstractValue multiply(NRAAbstractValue a,NRAAbstractValue b){return {a.magnitude+b.magnitude,a.precision+b.precision,a.infinite_precision||b.infinite_precision};}
 static NRAAbstractValue boolean(const z3::expr& e){NRAAbstractValue r{};for(unsigned i=0;i<e.num_args();++i)r=join(r,infer(e.arg(i)));return r;}
 static NRAAbstractValue constant(const z3::expr& e){const auto text=e.to_string();const double n=std::abs(std::strtod(text.c_str(),nullptr));const auto m=n<=1.0?1u:static_cast<uint32_t>(std::ceil(std::log2(n)))+1;const auto slash=text.find('/');if(slash==std::string::npos)return {m,1,false};uint64_t d=0;try{d=std::stoull(text.substr(slash+1));}catch(...){return {m,53,true};}uint32_t p=0;while(d>1&&d%2==0){d/=2;++p;}return {m,std::max(1u,p+1),d!=1};}
};
} // namespace SMT::Real
