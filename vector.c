/* Copyright (c) 2009-2011 Kyle Gorman
* 
*  Permission is hereby granted, free of charge, to any person obtaining a copy
*  of this software and associated documentation files (the "Software"), to deal
*  in the Software without restriction, including without limitation the rights
*  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
*  copies of the Software, and to permit persons to whom the Software is
*  furnished to do so, subject to the following conditions:
* 
*  The above copyright notice and this permission notice shall be included in
*  all copies or substantial portions of the Software.
* 
*  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
*  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
*  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
*  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
*  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
*  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
*  THE SOFTWARE.
*
*  vector: some data structures and mathematical function
*  Kyle Gorman <kgorman@ling.upenn.edu>
* 
*  If for some reason you didn't get vector.h, which you'll need to #include 
*  vector, it is available at:
*
*               http://ling.upenn.edu/~kgorman/c/vector.h       
* 
*  This is version 1.0., i.e. I think I got all obvious stuff working ideally. 
*/

#include <math.h>
#include <stdio.h>
#include <limits.h>
#include <string.h>
#include <stdlib.h>

#include "vector.h"

#ifndef NAN
    #define NAN     sqrt(-1.)
#endif

// create a vector of size xSz
vector makev(int xSz) {
    vector nw_vector;
    nw_vector.x = xSz;
    nw_vector.v = malloc(sizeof(double) * xSz);
    return(nw_vector);
}

// make a vector of zeros of size xSz
vector zerov(int xSz) { 
    int i;
    vector nw_vector = makev(xSz);
    for (i = 0; i < nw_vector.x; i++) {
        nw_vector.v[i] = 0.;
    }
    return(nw_vector); 
}

// make a vector of ones of size xSz
vector onesv(int xSz) { 
    int i;
    vector nw_vector = makev(xSz);
    for (i = 0; i < nw_vector.x; i++) {
        nw_vector.v[i] = 1.;
    }
    return(nw_vector); 
}

// make a vector of NaNs of size xSz
vector nansv(int xSz) { 
    int i;
    vector nw_vector = makev(xSz);
    for (i = 0; i < nw_vector.x; i++) {
        nw_vector.v[i] = NAN;
    }
    return(nw_vector); 
}

// make a deep copy of a vector
vector copyv(vector yr_vector) { 
    vector nw_vector = makev(yr_vector.x);
    memcpy(nw_vector.v, yr_vector.v, sizeof(double) * yr_vector.x);
    return(nw_vector);
}

// free the memory associated with the vector
void freev(vector yr_vector) { 
    free(yr_vector.v);
}

// print the vector
void printv(vector yr_vector) { 
    int i;
    for (i = 0; i < yr_vector.x; i++) {
        printf("%f\n", yr_vector.v[i]);
    }
}

// return the index of the maximum value of the vector
int maxv(vector yr_vector) {
    int i;
    int index;
    double val = SHRT_MIN;
    for (i = 0; i < yr_vector.x; i++) {
        if (yr_vector.v[i] > val) {
            val = yr_vector.v[i];
            index = i;
        }
    }
    return(index);
}

// return the index of the minimum value of the vector
int minv(vector yr_vector) { 
    int i;
    int index;
    double val = SHRT_MAX;
    for (i = 0; i < yr_vector.x; i++) {
        if (yr_vector.v[i] < val) {
            val = yr_vector.v[i];
            index = i;
        }
    }
    return(index);
}

// find the bisection index of the vector for key
int bisectv(vector yr_vector, double key) { 
    int md;                                
    int lo = 1;                           
    int hi = yr_vector.x;                   
    while (hi - lo > 1) {
        md = (hi + lo) >> 1;
        if (yr_vector.v[md] > key) {    
            hi = md;
        }
        else {
            lo = md;
        }
    }
    return(hi);
}

// like bisectv(), but the minimum starting value is passed as an argument. This
// is good for multiple bisection calls for forming a new vector when the 
// queries are a non-constant interval; but make sure to use bisectv() the 
// first time.
int bilookv(vector yr_vector, double key, int lo) { 
    int md;                                       
    int hi = yr_vector.x;                          
    lo--;                                         
    while (hi - lo > 1) {                         
        md = (hi + lo) >> 1;                      
        if (yr_vector.v[md] > key) {               
            hi = md; 
        }                                          
        else {
            lo = md;
        }
    }
    return(hi);
}

// intvector versions of the above

intvector makeiv(int xSz) {
    intvector nw_vector;
    nw_vector.x = xSz;
    nw_vector.v = malloc(sizeof(int) * xSz);
    return(nw_vector);
}

intvector zeroiv(int xSz) {
    int i;
    intvector nw_vector = makeiv(xSz);
    for (i = 0; i < nw_vector.x; i++) {
        nw_vector.v[i] = 0;
    }
    return(nw_vector);
}

intvector onesiv(int xSz) {
    int i;
    intvector nw_vector = makeiv(xSz);
    for (i = 0; i < nw_vector.x; i++) {
        nw_vector.v[i] = 1;
    }
    return(nw_vector);
}

intvector copyiv(intvector yr_vector) { 
    int i;
    intvector nw_vector = makeiv(yr_vector.x);
    memcpy(nw_vector.v, yr_vector.v, sizeof(int) * nw_vector.x);
    return(nw_vector);
}

// convert an intvector into a vector using implicit casts to double
vector iv2v(intvector yr_vector) {
    int i; 
    vector nw_vector = makev(yr_vector.x);
    for (i = 0; i < yr_vector.x; i++) {
        nw_vector.v[i] = yr_vector.v[i]; 
    }
    return(nw_vector);
}

void freeiv(intvector yr_vector) {
    free(yr_vector.v);
}

void printiv(intvector yr_vector) {
    int i;
    for (i = 0; i < yr_vector.x; i++) {
        printf("%d\n", yr_vector.v[i]);
    }
}

int maxiv(intvector yr_vector) { 
    int i;
    int index;
    int val = SHRT_MIN;
    for (i = 0; i < yr_vector.x; i++) {
        if (yr_vector.v[i] > val) {
            val = yr_vector.v[i];
            index = i;
        }
    }
    return(index);
}

int miniv(intvector yr_vector) {
    int i;
    int index;
    int val = SHRT_MAX;
    for (i = 0; i < yr_vector.x; i++) {
        if (yr_vector.v[i] < val) {
            val = yr_vector.v[i];
            index = i;
        }
    }
    return(index);
}

int bisectiv(intvector yr_vector, int key) {
    int md;                                
    int lo = 1;                            
    int hi = yr_vector.x;                    
    while (hi - lo > 1) {
        md = (hi + lo) >> 1;
        if (yr_vector.v[md] > key) {    
            hi = md;
        }
        else {
            lo = md;
        }
    }
    return(hi);
}

int bilookiv(intvector yr_vector, int key, int lo) {
    int md;                                
    int hi = yr_vector.x;                    
    lo--;
    while (hi - lo > 1) {
        md = (hi + lo) >> 1;
        if (yr_vector.v[md] > key) {    
            hi = md;
        }
        else {
            lo = md;
        }
    }
    return(hi);
}

// matrix versions of the above

matrix makem(int xSz, int ySz) {
    int i;
    matrix nw_matrix;
    nw_matrix.x = xSz;
    nw_matrix.y = ySz;
    nw_matrix.m = malloc(sizeof(double*) * xSz);
    for (i = 0; i < nw_matrix.x; i++) {
        nw_matrix.m[i] = malloc(sizeof(double) * ySz);
    }
    return(nw_matrix);
}

matrix zerom(int xSz, int ySz) { 
    int i;
    int j;
    matrix nw_matrix = makem(xSz, ySz);
    for (i = 0; i < nw_matrix.x; i++) {
        for (j = 0; j < nw_matrix.y; j++) {
            nw_matrix.m[i][j] = 0.;
        }
    }
    return(nw_matrix);
}

matrix onesm(int xSz, int ySz) { 
    int i; 
    int j;
    matrix nw_matrix = makem(xSz, ySz);
    for (i = 0; i < nw_matrix.x; i++) {
        for (j = 0; j < nw_matrix.y; j++) {
            nw_matrix.m[i][j] = 1.;
        }
    }
    return(nw_matrix);
}

matrix nansm(int xSz, int ySz) { 
    int i;
    int j;
    matrix nw_matrix = makem(xSz, ySz);
    for (i = 0; i < nw_matrix.x; i++) {
        for (j = 0; j < nw_matrix.y; j++) {
            nw_matrix.m[i][j] = NAN;
        }
    }
    return(nw_matrix);
}

matrix copym(matrix yr_matrix) {
    int i;
    matrix nw_matrix = makem(yr_matrix.x, yr_matrix.y);
    for (i = 0; i < yr_matrix.x; i++) { // does not assume contiguous memory
        memcpy(nw_matrix.m[i], yr_matrix.m[i], sizeof(double) * yr_matrix.y);
    }
    return(nw_matrix);
}

void freem(matrix yr_matrix) {
    int i;
    for (i = 0; i < yr_matrix.x; i++) {
        free(yr_matrix.m[i]);
    }
    free(yr_matrix.m);
}

void printm(matrix yr_matrix) {
    int i;
    int j;
    for (i = 0; i < yr_matrix.x; i++) {
        for (j = 0; j < yr_matrix.y; j++) {
            printf("%f\t", yr_matrix.m[i][j]);
        }
        printf("\n");
    }
}

// intmatrix versions of the above

intmatrix makeim(int xSz, int ySz) {
    intmatrix nw_matrix;
    nw_matrix.x = xSz;
    nw_matrix.y = ySz;
    nw_matrix.m = malloc(sizeof(int) * xSz);
    int i;
    for (i = 0; i < nw_matrix.x; i++) {
        nw_matrix.m[i] = malloc(sizeof(int) * ySz);
    }
    return(nw_matrix);
}

intmatrix zeroim(int xSz, int ySz) { 
    int i; 
    int j;
    intmatrix nw_matrix = makeim(xSz, ySz);
    for (i = 0; i < nw_matrix.x; i++) {
        for (j = 0; j < nw_matrix.y; j++) {
            nw_matrix.m[i][j] = 0;
        }
    }
    return(nw_matrix);
}

intmatrix onesim(int xSz, int ySz) { 
    int i;
    int j;
    intmatrix nw_matrix = makeim(xSz, ySz);
    for (i = 0; i < nw_matrix.x; i++) {
        for (j = 0; j < nw_matrix.y; j++) {
            nw_matrix.m[i][j] = 1;
        }
    }
    return(nw_matrix);
}

intmatrix copyim(intmatrix yr_matrix) { 
    int i;
    intmatrix nw_matrix = makeim(yr_matrix.x, yr_matrix.y);
    for (i = 0; i < yr_matrix.x; i++) { // NB: does not assume contiguous memory
        memcpy(nw_matrix.m[i], yr_matrix.m[i], sizeof(int) * yr_matrix.y);
    }
    return(nw_matrix);
}

matrix im2m(intmatrix yr_matrix) {
    int i;
    int j;
    matrix nw_matrix = makem(yr_matrix.x, yr_matrix.y);
    for (i = 0; i < yr_matrix.x; i++) {
        for (j = 0; j < yr_matrix.y; j++) {
            nw_matrix.m[i][j] = yr_matrix.m[i][j]; 
        }
    }
}

void freeim(intmatrix yr_matrix) {
    int i;
    for (i = 0; i < yr_matrix.x; i++) {
        free(yr_matrix.m[i]);
    }
    free(yr_matrix.m);
}

void printim(intmatrix yr_matrix) {
    int i; 
    int j;
    for (i = 0; i < yr_matrix.x; i++) {
        for (j = 0; j < yr_matrix.y; j++) {
            printf("%d\t", yr_matrix.m[i][j]);
        }
        printf("\n");
    }
}

// a naive Sieve of Erasthones for prime numbers
int sieve(intvector ones) {
    int i;
    int j;
    int k = 0;
    int sp = floor(sqrt(ones.x));
    ones.v[0] = NP; // Because 1 is not prime (though sometimes we wish it was)
    for (i = 1; i < sp; i++) { 
        if PRIME(ones.v[i]) {
            for (j = i + i + 1; j < ones.x; j += i + 1) {
                ones.v[j] = NP; // Mark it not prime
            }
            k++;
        }
    }
    for (i = sp; i < ones.x; i++) { // Now we're only counting
        if PRIME(ones.v[i]) {
            k++;
        }
    }
    return(k); 
}

intvector primes(int n) {
    int i;
    int j = 0;
    intvector myOnes = onesiv(n);
    intvector myPrimes = makeiv(sieve(myOnes)); // size of the # of primes
    for (i = 0; i < myOnes.x; i++) { // could start at 1, unless we're hacking
        if PRIME(myOnes.v[i]) {
            myPrimes.v[j++] = i + 1;
        }
    }
    freeiv(myOnes);
    return(myPrimes);
}


// cubic spline function, based on Numerical Recipes in C, 2nd ed.
vector spline(vector x, vector y) {
    int i;
    int j;
    double p;
    double un;
    double qn;
    double sig;
    vector y2 = makev(x.x);
    double* u = malloc((unsigned) (x.x - 1) * sizeof(double));
    y2.v[0] = -.5; // Left boundary
    u[0] = (3. / (x.v[1] - x.v[0])) * ((y.v[1] - y.v[0]) /
                                       (x.v[1] - x.v[0]) - YP1);
    for (i = 1; i < x.x - 1; i++) { // Decomp loop
        sig = (x.v[i] - x.v[i - 1]) / (x.v[i + 1] - x.v[i - 1]);
        p = sig * y2.v[i - 1] + 2.;
        y2.v[i] = (sig - 1.) / p;
        u[i] = (y.v[i + 1] - y.v[i]) / (x.v[i + 1] - x.v[i]) -
                                  (y.v[i] - y.v[i - 1]) / (x.v[i] - x.v[i - 1]);
        u[i] = (6. * u[i] / (x.v[i + 1] - x.v[i - 1]) - sig * u[i - 1]) / p;
    }
    qn = .5; // Right boundary
    y2.v[y2.x - 1] = ((3. / (x.v[x.x - 1] - x.v[x.x - 2])) * (YPN -
                               (y.v[y.x - 1] - y.v[y.x -  2]) / (x.v[x.x - 1] -
                                    x.v[x.x - 2])) - qn * u[x.x - 2]) /         
                                             (qn * y2.v[y2.x - 2] + 1.);
    for (j = x.x - 2; j >= 0; j--) { // Backsubstitution loop
        y2.v[j] = y2.v[j] * y2.v[j + 1] + u[j];
    }
    free(u); 
    return(y2);
}

// query the cubic spline
double splinv(vector x, vector y, vector y2, double val, int hi) {
    double h;
    double b;
    double a;
    int lo = hi - 1; // find hi linearly, or using bisectv()
    h = x.v[hi] - x.v[lo];
    a = (x.v[hi] - val) / h;
    b = (val - x.v[lo]) / h; 
    return(a * y.v[lo] + b * y.v[hi] + ((a * a * a - a) * y2.v[lo] *
                                  (b * b * b - b) * y2.v[hi]) * (h * h) / 6.);
}

// polynomial fitting with CLAPACK: solves poly(A, m) * X = B
vector polyfit(vector A, vector B, int order) { 
    int i;                                      
    int j;
    int info;
    order++; // I find it intuitive this way...
    double* Ap = malloc(sizeof(double) * order * A.x); // Build up the A matrix
    for (i = 0; i < order; i++) {                      // as a vector in column-
        for (j = 0; j < A.x; j++) {                    // major-order.
            Ap[i * A.x + j] = pow(A.v[j], order - i - 1); // Mimics MATLAB
        }
    }
    vector Bp = makev(order >= B.x ? order : B.x); 
    for (i = 0; i < B.x; i++) {
        Bp.v[i] = B.v[i];
    }
    i = 1; // nrhs, j is info
    j = A.x + order; // lwork
    double* work = malloc(sizeof(double) * j);
    dgels_("N", &A.x, &order, &i, Ap, &B.x, Bp.v, &order, work, &j, &info);
    free(Ap);
    if (info < 0) {
        fprintf(stderr, "LAPACK routine dgels() returns error: %d\n", info);
        exit(EXIT_FAILURE);
    }
    else { 
        return(Bp);
    }
}

// given a vector of coefficients and a value for x, evaluate the polynomial
double polyval(vector coefs, double val) { 
    int i;                                 
    double sum = 0.;                       
    for (i = 0; i < coefs.x; i++) {
        sum += coefs.v[i] * pow(val, coefs.x  - i - 1);
    }
    return(sum);
}

// some test code
#ifdef DEBUG
int main(void) {

    int i
    int j;

    printf("VECTOR example\n");
    vector a = makev(10);    
    for (i = 0; i < a.x; i++) {
        a.v[i] = i * i;
    }
    vector b = copyv(a);
    printv(b);
    freev(a);
    freev(b);
    printf("\n");
    
    printf("INTVECTOR example\n");
    intvector c = makeiv(10);    
    for (i = 0; i < c.x; i++) {
        c.v[i] = i * i;
    }
    intvector d = copyiv(c);
    printiv(d);
    freeiv(c);
    freeiv(d);
    printf("\n");
    
    printf("more INTVECTOR\n");
    intvector c1 = zeroiv(10);
    printiv(c1);
    freeiv(c1);
    intvector d1 = onesiv(10);
    printiv(d1);
    freeiv(d1);
    printf("\n");

    printf("MATRIX example\n");
    matrix e = makem(20, 3);
    for (i = 0; i < e.x; i++) {
        for (j = 0; j < e.y; j++) {
            e.m[i][j] = i * i + j;
        }
    }
    matrix f = copym(e);
    printm(f);
    freem(e);
    freem(f);
    printf("\n");

    printf("INTMATRIX example\n");
    intmatrix g = makeim(20, 3);
    for (i = 0; i < g.x; i++) {
        for (j = 0; j < g.y; j++) {
            g.m[i][j] = i * i + j;
        }
    }
    intmatrix h = copyim(g);
    printim(h);
    freeim(g);
    freeim(h);
    printf("\n");

    printf("SIEVE example (input: 23)\n");
    printiv(primes(23));
    printf("\n");

    printf("BILOOK example\n");
    vector fives = makev(300); 
    for (i = 0; i < fives.x; i++) { 
        fives.v[i] = (i + 10) * 5.;
    }
    vector twenties = makev(100);
    for (i = 0; i < twenties.x; i++) {
        twenties.v[i] = i * 20.;
    }
    printf("searching for values of vector fives in twenties...\n");
    printf("fives (sz:%d): %f < x < %f\n", fives.x, fives.v[minv(fives)], 
                                                    fives.v[maxv(fives)]);
    printf("twenties (sz:%d): %f < x < %f\n", twenties.x, 
                                              twenties.v[minv(twenties)], 
                                              twenties.v[maxv(twenties)]);
    int hi = bisectv(twenties, fives.v[14]);
    for (i = 15; i < 30; i++) {
        hi = bilookv(twenties, fives.v[i], hi - 1);
        printf("twenties[%d] %f <= fives[%d] %f < twenties[%d] %f\n", hi - 1, 
                         twenties.v[hi - 1], i, fives.v[i], hi, twenties.v[hi]);
    }
    freev(fives);
    freev(twenties);
    printf("\n");

    printf("POLY example\n");
    vector x = makev(4); 
    vector y = makev(4); 
    x.v[0] = 3.0;
    x.v[1] = 1.5;
    x.v[2] = 4.0;
    x.v[3] = 2.;
    y.v[0] = 2.5;
    y.v[1] = 3.1;
    y.v[2] = 2.1;
    y.v[3] = 1.0;
    printv(polyfit(x, y, 4));
    printf("\nOctave sez: -0.683446 5.276186 -10.846127 -0.092885 13.295935\n");
    printf("%f\n", polyval(polyfit(x, y, 4), 3));
    printf("Octave sez: 2.5\n\n");

}
#endif
