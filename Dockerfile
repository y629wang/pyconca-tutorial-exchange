FROM ankitml/python3.7
ADD . /code
WORKDIR /code
RUN pip install -Ur requirements.txt
