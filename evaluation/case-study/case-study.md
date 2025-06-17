# Technical Report of Evaluation

## Queries

### Regular Templates 
We have the following regular template:

    Q1: "a*",
    Q2: "ab*",
    Q3: "a?b*",
    Q4: "ab",
    Q5: "a*/b*",
    Q6: "a*/b*/c",
    Q7: "a/b/c",
    Q8: "a/b*/c",
    Q9: "(a | b | c)*",
    Q10: "(a | b |c)/b*"

### Data Constraint: 
We instantiate five data constraints into the regular expressions

+ D1. Assert that the distance between an attribute and a constant should be within a threshold, i.e. exists a parameter p, such that 
    

        |?p - attr| < constant

   And the equal data constraint is:

         ?p - attr < c and attr - ?p < c 

+ D2. Query the upper and lower bound of an attribute `attr', i.e.


        ?p >= attr and ?q <= attr

+ D3. Query a path, such that the upper and lower bound of an attribute should be within a threshold. i.e.

        ?p >= attr and ?q <= attr and ?p - ?q < c

+ D4. This query is inspired by the dating query in Geri's thesis. Query a path, such that:

    Let the start point satisfy the  following condition:


         |?p - attr1| < c and ?q == attr2 


    And the successor nodes should satisfy the following condition: 


         |?p - attr1| < c and attr2 * 0.5 + 10 <= ?q
    
    And we can also expand the absolute value by:
            
            
             attr1 - ?p < c and ?p - attr < c


+ D5. The 2-D manhattan distance between  $(a_1, b_1)$  and $(a_2, b_2)$ is defined as following:
            $$MH = |a_1 - a_2 | + |b_1 - b_2|$$

We want to assert the manattan distance from the start point of a path to all nodes along the path within a threshold. $MH < c$. 

We can use two global parameters to encode the mahattan distance between the start point and the successor along a path: 
     For the start point, let ?p and ?q as two parameters, we have 
        
        ?p == attr1 and ?q = attr2
     
     
     
For the successor nodes along the path, we have 

    ?p - attr1 + ?q - attr2 < c and 
    ?p - attr1 + attr2 - ?q < c and 
    attr1 - ?p + ?q - attr2 < c and 
    attr1 - ?p + attr2 - ?q < c 

## Experiment Setup
The experiment was run on a ubuntu subsystem on a windows 11 Laptop with i7-13700H Core CPU and 16 GB assigned memories. The following table shows the stat of each dataset. 


| Dataset      | Node Number  | Edge Number   | Queries for Each Template| Queries in Total
| -----------  | -----------  |------|------ | -----|
| ICIJ-Leak    | 1908466   |   3193390   |  10000 | 500000 
| Pokec        |      1632803   |   30622564   | 10000 | 500000
| LDBC10       |  29987850 | 178101408 | 10000 | 500000
| ICIJ-Paradise|   163414 |   364456 | 1000 | 50000
| Telecom      |  170k    | 50M      | 1000  | 50000
| LDBC01       | 184329 | 767894| 1000 | 50000

## Evaluation Result:

### LDBC01 Dataset

#### Time Performace
The following table shows statistics of regular path querie for each template. 

| Regular Expression | Averge Time(ms) | Maximal Time(ms)
| ------------------|------------------|-----------------|
a* |0.32| 10.6
ab* |0.32| 15.63
a?b* |0.35| 0.9
ab |0.41| 0.87
a*/b* |0.36| 0.84
a*/b*/c |0.32| 21.99
a/b/c |0.32| 0.72
a/b*/c |0.25| 0.72
(a \| b \| c)* |0.26| 0.63
(a \| b \|c)/b* |0.26| 0.57



The following tables shows the statistics of RDPQ for each regular template with different data test conditions. 

<div style="display: inline-block; width: 48%; margin-right: 2%; vertical-align: top;">

**Template a***  

|  | Averge Time(ms) | Max Time(ms)|
|-----|-----|---|
D1 |1.75| 48.13
D2 |1.36| 2.22
D3 |1.51| 2.98
D4 |2.01| 17.51
D5 |2.71| 23.36
</div>
<div style="display: inline-block; width: 48%; vertical-align: top;">

**Template ab***  

|  | Averge Time(ms) | Max Time(ms)|
|-----|-----|---|
D1 |1.64| 16.44
D2 |1.56| 16.68
D3 |2.41| 16.73
D4 |2.21| 16.29
D5 |3.29| 25.01

</div>

<div style="display: inline-block; width: 48%; margin-right: 2%; vertical-align: top;">

**Template a?b***  

|  | Averge Time(ms) | Max Time(ms)|
|-----|-----|---|
D1 |1.79| 16.82
D2 |1.72| 3.68
D3 |3.89| 17.26
D4 |3.31| 15.8
D5 |5.0| 21.89
</div>
<div style="display: inline-block; width: 48%; vertical-align: top;">

**Template ab**  

|  | Averge Time(ms) | Max Time(ms)|
|-----|-----|---|
D1 |5.39| 55.54
D2 |5.31| 64.93
D3 |6.17| 95.32
D4 |2.27| 17.17
D5 |3.36| 20.31

</div><div style="display: inline-block; width: 48%; margin-right: 2%; vertical-align: top;">

**Template a*/b***  

|  | Averge Time (ms)| Max Time(ms)|
|-----|-----|---|
D1 |1.79| 17.39
D2 |1.78| 4.26
D3 |4.03| 15.92
D4 |3.4| 15.75
D5 |5.02| 24.11
</div>
<div style="display: inline-block; width: 48%; vertical-align: top;">

**Template a*/b*/c**  

|  | Averge Time (ms)| Max Time(ms)|
|-----|-----|---|
D1 |5.49| 57.55
D2 |5.1| 51.67
D3 |2.73| 17.28
D4 |2.6| 16.82
D5 |3.53| 18.52

</div>

<div style="display: inline-block; width: 48%; margin-right: 2%; vertical-align: top;">

**Template a/b/c**  

|  | Averge Time (ms)| Max Time(ms)|
|-----|-----|---|
D1 |102.42| 3247.44
D2 |89.33| 2808.95
D3 |2.33| 12.68
D4 |2.22| 9.24
D5 |3.0| 20.61

</div>
<div style="display: inline-block; width: 48%; vertical-align: top;">

**Template a/b*/c**  

|  | Averge Time (ms)| Max Time(ms)|
|-----|-----|---|
D1 |89.72| 2999.95
D2 |153.27| 4416.9
D3 |2.16| 12.94
D4 |2.11| 12.96
D5 |2.91| 19.5

</div>

<div style="display: inline-block; width: 48%; margin-right: 2%; vertical-align: top;">

**Template (a|b|c)***  

|  | Averge Time(ms) | Max Time(ms)|
|-----|-----|---|
D1 |6.67| 26.23
D2 |9.11| 53.4
D3 |3.69| 14.09
D4 |3.21| 16.34
D5 |4.54| 18.95
</div>
<div style="display: inline-block; width: 48%; vertical-align: top;">

**Template  (a|b|c)/b***  

|  | Averge Time(ms) | Max Time(ms)|
|-----|-----|---|
D1 |1.64| 16.44
D2 |1.56| 16.68
D3 |2.41| 16.73
D4 |2.21| 16.29
D5 |3.29| 25.01

</div>
The following box figure show the distribution of running time on LDBC01 dataset


<img src="figure/LDBC01-time.svg" alt="SVG 图片" width="2000">



## Average SMT Formulas Checked Each Step:

It is a constant 3, since we have insert the same formula to each atom of regular expressions. 

Problem: how to take make-sense queries without change the semantics of regular expression. 

For example. if we want to test the difference of $attr$ between two objects less or equal than 5, we need 

    ?p = attr and ?q < attr /( ?p > attr > ?q)* /
     ?p > attr and ?q = attr and ?p - ?q < 5

    /*We omit the labels of objects */

We can not instantiate such formula to regex end with $*$



## Alternative Metric: The Cardinality of the Exploration Tree

The following bar figures present tha stata of exploration tree cardinalities of each regular expression with different data constraint on each data set. The x-axis represent the cardinality of exploration tree, and the y-axis represent the number of queries. I also use logarithm coordinate for the y-axis.


<img src="figure/icij-step.svg" alt="SVG 图片" width="2000">

<img src="figure/pokec-step.svg" alt="SVG 图片" width="2000">

<img src="figure/paradise-step.svg" alt="SVG 图片" width="2000">

<img src="figure/telecom-step.svg" alt="SVG 图片" width="2000">