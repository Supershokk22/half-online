@echo off
echo Example:
echo py peer_agent.py --server ws://100.X.X.X:8790 --room teste --name SeuNome --role host
echo.
py "%~dp0peer_agent.py" %*
