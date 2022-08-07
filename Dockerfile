FROM jupyter/scipy-notebook:0fd03d9356de

RUN pip install --upgrade pip
RUN pip install websocket-client
RUN pip install pandas_ta
RUN pip install python-binance
RUN pip install yfinance