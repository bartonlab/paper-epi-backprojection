#ifndef INF_H_DECON
#define INF_H_DECON

#include <vector>
#include <string>
#include <stdio.h>


// Typedefs
typedef std::vector<std::vector<double> > Vector;
typedef std::vector<std::vector<int> > IntVector;
typedef std::vector<std::vector<std::vector<double> > > VVector;
typedef std::vector<std::vector<std::vector<int> > > IntVVector;


// PROGRAM SETTINGS - This class holds the parameters needed for running the algorithm

class RunParameters {
    
public:
    
    std::string directory;             // path to the directory where the input file is located
                                       // output will also be sent to this directory
    std::vector<std::string> infiles;  // input file list
    std::string muInfile;              // input file for mutation matrix
    std::string outfile;               // output file
    std::string covOutfile;            // output file for the regularized integrated covariance matrix
    std::string numOutfile;            // output file for the "numerator" (change in mutant frequency + mutation term)
    
    double tol;             // maximum tolerance for covariance differences before interpolating
    double gamma;           // Gaussian regularization strength
    double N;               // population size
    double mu;              // mutation rate per generation
    int q;                  // number of states for each allele
    
    bool useMatrix;         // if true, read mutation matrix from file
    bool useCovariance;     // if true, include covariance (linkage) information, else default to independent sites
    bool useAsymptotic;     // if true, assume that sequences are collected over long times (equilibrium)
    bool useVerbose;        // if true, print extra information while program is running
    bool saveCovariance;    // if true, output the total covariance matrix
    bool saveNumerator;     // if true, output the "numerator" multiplying the inverse covariance

    
    RunParameters() {
        
        directory = ".";
        muInfile  = "mu.dat";
        outfile   = "output.dat";
        
        tol   = 0.05;
        gamma = 1.0;
        N     = 1.0e4;
        mu    = 1.0e-4;
        q     = 2;
        
        useMatrix      = false;
        useCovariance  = true;
        useAsymptotic  = false;
        useVerbose     = false;
        saveCovariance = false;
        saveNumerator  = false;
        
    }
    std::string getSequenceInfile()              { return (directory+"/"+infiles[0]);  }
    std::string getSequenceInfile(int i)         { return (directory+"/"+infiles[i]);  }
    std::string getMuInfile()                    { return (directory+"/"+muInfile);    }
    std::string getSelectionCoefficientOutfile() { return (directory+"/"+outfile);     }
    std::string getCovarianceOutfile()           { return (directory+"/"+covOutfile);  }
    std::string getNumeratorOutfile()            { return (directory+"/"+numOutfile);  }
    ~RunParameters() {}
    
};


// Main program
int run(RunParameters &r);

// Auxiliary routines
void computeAlleleFrequencies(const IntVector &sequences, const std::vector<double> &counts, int q, std::vector<double> &p1, std::vector<double> &p2);
void interpolateFrequencies(const std::vector<double> &p1_0, const std::vector<double> &p2_0, const std::vector<double> &p1_1, const std::vector<double> &p2_1, double x, std::vector<double> &p1, std::vector<double> &p2);
void updateCovariance(double dg, const std::vector<double> &p1, const std::vector<double> &p2, std::vector<double> &totalCov);
void updateCovarianceIntegrate(double dg, const std::vector<double> &p1_0, const Vector &p2_0, const std::vector<double> &p1_1, const Vector &p2_1, Vector &totalCov);
void updateMu(double dg, const Vector &muMatrix, const std::vector<double> &p1, std::vector<double> &totalMu);
void updateMu(double dg, const std::vector<double> &p1, std::vector<double> &totalMu);
void updateMuIntegrate(double dg, const Vector &muMatrix, const std::vector<double> &p1_0, const std::vector<double> &p1_1, std::vector<double> &totalMu);
void processAsymptotic(const IntVVector &sequences, const Vector &counts, const Vector &muMatrix, int q, std::vector<double> &totalCov, std::vector<double> &dx);
void processStandard(const IntVVector &sequences, const Vector &counts, const std::vector<double> &times, const Vector &muMatrix, int q, std::vector<double> &totalCov, std::vector<double> &dx);
void regularizeCovariance(const IntVVector &sequences, int q, double gammaN, bool useCovariance, std::vector<double> &totalCov);


// For j>i, the pair {i,j} in the list {{0,1}, {0,2}, ... } is located at offset(i, length)+j

inline int offset(int i, size_t length) {
    
    return (int) (length + i * (length - 2) - (i * (i - 1)) / 2 - 1);
    
}


// For j>i, the pair {i, j} in the list {{0,0}, {0,1}, ... } is located at hindex(i, j, length)
// This routine is necessary when the diagonal term is also included

inline int hindex(int i, int j, size_t length) {
    
    return (int) (i * length - (i * (i + 1)) / 2 + j);
    
}


// Returns as above, but with a check to make sure that j>i

inline int safeHindex(int i, int j, size_t length) {
    
    if (j>i) return (int) (i * length - (i * (i + 1)) / 2 + j);
    else     return (int) (j * length - (j * (j + 1)) / 2 + i);
    
}


#endif
