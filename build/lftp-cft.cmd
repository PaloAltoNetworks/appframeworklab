set ftps:initial-prot "";
set ftp:ssl-force true;
set ftp:ssl-protect-data true;
open ftps://ftp.box.com:990
user BOXUSER BOXPASSWORD
cd "GitUpload";
put "cft/appframework-lab.json";
put "cft/apiexplorer-cft.json";
