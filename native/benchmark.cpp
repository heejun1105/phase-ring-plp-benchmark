// Separate fused, preallocated C++ CPU study. No physical PIM measurements.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <complex>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

using C=std::complex<float>;
struct Q15{int16_t re,im;};
inline C decode(Q15 x){return C(float(x.re)/32767,float(x.im)/32767);}
constexpr double tau=6.283185307179586476925286766559;
volatile double checksum_sink=0;
uint16_t quant(double x,int n){return uint16_t(int(std::floor(x*n/tau)))&uint16_t(n-1);}

int main(int argc,char** argv){
    const std::string folder=argc>1?argv[1]:"results";
    std::ofstream raw(folder+"/native_samples.csv"),summary(folder+"/native_benchmark.csv"),accuracy(folder+"/native_accuracy.csv");
    raw<<"n,method,repeat,elapsed_ms\n";
    summary<<"n,method,mean_ms,median_ms,std_ms,min_ms,max_ms,repeats,warmups,ops_per_sec\n";
    accuracy<<"n,method,evaluated_samples,angular_rmse_rad,max_angular_error_rad\n";
    raw<<std::setprecision(14);summary<<std::setprecision(14);accuracy<<std::setprecision(14);
    for(auto size:{10000,100000,1000000,10000000}){
        std::mt19937 gen(20261020);std::uniform_real_distribution<double> dist(-tau/2,tau/2);
        std::vector<double>a(size),b(size);std::vector<C>x(size),y(size),out(size);
        std::vector<uint16_t>qa[2],qb[2],index(size);
        std::vector<Q15>lut[2];
        for(int j=0;j<2;j++){
            int n=1024<<j;qa[j].resize(size);qb[j].resize(size);lut[j].resize(n);
            for(int k=0;k<n;k++){
                int16_t re=int16_t(std::cos(k*tau/n)*32767),im=int16_t(std::sin(k*tau/n)*32767);
                lut[j][k]=Q15{re,im};
            }
        }
        for(int i=0;i<size;i++){
            a[i]=dist(gen);b[i]=dist(gen);x[i]=C(std::cos(a[i]),std::sin(a[i]));y[i]=C(std::cos(b[i]),std::sin(b[i]));
            for(int j=0;j<2;j++){qa[j][i]=quant(a[i],1024<<j);qb[j][i]=quant(b[i],1024<<j);}
        }
        struct Task{std::string name;std::function<void()> fn;bool integer;std::vector<double> samples;};
        std::vector<Task> tasks;
        tasks.push_back({"FP32 kernel",[&](){for(int i=0;i<size;i++)out[i]=x[i]*y[i];},false,{}});
        tasks.push_back({"FP32 end-to-end",[&](){for(int i=0;i<size;i++)out[i]=C(std::cos(a[i]),std::sin(a[i]))*C(std::cos(b[i]),std::sin(b[i]));},false,{}});
        for(int j=0;j<2;j++){
            int n=1024<<j;
            tasks.push_back({"Z"+std::to_string(n)+" add",[&,j,n](){for(int i=0;i<size;i++)index[i]=(qa[j][i]+qb[j][i])&(n-1);},true,{}});
            tasks.push_back({"Z"+std::to_string(n)+" encoded-to-complex",[&,j,n](){for(int i=0;i<size;i++)out[i]=decode(lut[j][(qa[j][i]+qb[j][i])&(n-1)]);},false,{}});
            tasks.push_back({"Z"+std::to_string(n)+" end-to-end",[&,j,n](){for(int i=0;i<size;i++)out[i]=decode(lut[j][(quant(a[i],n)+quant(b[i],n))&(n-1)]);},false,{}});
        }
        auto consume=[&](bool integer){
            double sum=0;if(integer)for(auto v:index)sum+=v;else for(auto v:out)sum+=v.real()+v.imag();
            checksum_sink=checksum_sink+sum;
        };
        for(auto& task:tasks)for(int warm=0;warm<2;warm++){task.fn();consume(task.integer);}
        std::vector<int>order(tasks.size());std::iota(order.begin(),order.end(),0);
        for(int repeat=0;repeat<7;repeat++){
            std::shuffle(order.begin(),order.end(),gen);
            for(int k:order){auto& task=tasks[k];auto start=std::chrono::steady_clock::now();task.fn();
                double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
                task.samples.push_back(ms);raw<<size<<','<<task.name<<','<<repeat<<','<<ms<<'\n';consume(task.integer);}
        }
        for(auto& task:tasks){
            auto v=task.samples;std::sort(v.begin(),v.end());double mean=std::accumulate(v.begin(),v.end(),0.0)/v.size(),ss=0;
            for(double z:v)ss+=(z-mean)*(z-mean);
            summary<<size<<','<<task.name<<','<<mean<<','<<v[v.size()/2]<<','<<std::sqrt(ss/(v.size()-1))<<','<<v.front()<<','<<v.back()<<",7,2,"<<size/(v[v.size()/2]/1000)<<'\n';
            if(task.name=="FP32 kernel" || task.name=="Z1024 encoded-to-complex" || task.name=="Z2048 encoded-to-complex"){
                task.fn();double sum=0,maxerr=0;int count=std::min(size,200000);
                for(int i=0;i<count;i++){
                    double angle=std::atan2(double(out[i].imag()),double(out[i].real()));
                    double e=std::abs(std::remainder(angle-a[i]-b[i],tau));sum+=e*e;maxerr=std::max(maxerr,e);
                }
                accuracy<<size<<','<<task.name<<','<<count<<','<<std::sqrt(sum/count)<<','<<maxerr<<'\n';
            }
        }
        std::cout<<"Native CPU measurements complete: "<<size<<std::endl;
    }
    std::cout<<"Checksum: "<<checksum_sink<<std::endl;
    return raw && summary && accuracy ? 0 : 1;
}
