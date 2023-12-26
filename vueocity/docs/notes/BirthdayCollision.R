digits = 8
sample_start = 100
sample_end = 100000
values = ( 26 + 26 + 10 ) ** digits
n = sample_start:sample_end
plot(n,1 - ((values-1)/values)^(n*(n-1)/2), type='l')
