FROM jupyter/scipy-notebook:0fd03d9356de

RUN pip install --upgrade pip
RUN pip install websocket-client
RUN pip install ta
RUN pip install python-binance
