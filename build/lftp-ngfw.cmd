set ftps:initial-prot "";
set ftp:ssl-force true;
set ftp:ssl-protect-data true;
open ftps://ftp.box.com:990
user BOXUSER BOXPASSWORD
cd Business\ Development\ -\ Shared/Francesco/RefAppCFTBuckets;
put buckets/appframework-ngfw.zip
