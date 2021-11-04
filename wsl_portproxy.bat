
FOR /F "tokens=* USEBACKQ" %%F IN (`wsl hostname -I`) DO (
SET ADDRESS=%%F
)
netsh interface portproxy add v4tov4 listenport=443 listenaddress=0.0.0.0 connectport=443 connectaddress=%ADDRESS%
