#!/bin/sh
# Performs 5 curls to http/https versions of sites and dumps all stats
echo 'http_code,http_connect,num_connects,num_redirects,size_download,size_header,size_request,size_upload,time_connect,time_namelookup,time_pretransfer,time_redirect,time_starttransfer,time_total,url_effective'

for i in {1..5}
do
	curl -L -w '%{http_code},%{http_connect},%{num_connects},%{num_redirects},%{size_download},%{size_header},%{size_request},%{size_upload},%{time_connect},%{time_namelookup},%{time_pretransfer},%{time_redirect},%{time_starttransfer},%{time_total},%{url_effective}\n' -o /dev/null -s "http://$1"

	curl -L -w '%{http_code},%{http_connect},%{num_connects},%{num_redirects},%{size_download},%{size_header},%{size_request},%{size_upload},%{time_connect},%{time_namelookup},%{time_pretransfer},%{time_redirect},%{time_starttransfer},%{time_total},%{url_effective}\n' -o /dev/null -s "https://$1"
done
