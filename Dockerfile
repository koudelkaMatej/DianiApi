#FROM ubuntu:20.04
#LABEL maintainer="Koudelka Matej"
#RUN apt-get update -y && \
#apt-get install -y python3-pip python3-dev
#COPY requirements.txt requirements.txt
#WORKDIR /python-docker
#RUN pip install -r requirements.txt
#COPY . .
#EXPOSE 5000
#ENTRYPOINT ["python3"]
#CMD ["./app.py"]

# load python 3.8 dependencies using slim debian 10 image.
FROM python:3.8-slim-buster
# build variables.
ENV DEBIAN_FRONTEND noninteractive
# install Microsoft SQL Server requirements.
ENV ACCEPT_EULA=Y
RUN apt-get update -y && apt-get update \
  && apt-get install -y --no-install-recommends curl gcc g++ gnupg unixodbc-dev
# Add SQL Server ODBC Driver 17 for Ubuntu 18.04
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
  && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends --allow-unauthenticated msodbcsql17 mssql-tools \
  && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile \
  && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc


WORKDIR /python-docker
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]