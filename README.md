# IceDrive Authentication service 
Repositoriy URL for the authetication service: https://github.com/AlejandroHoyo/distributed-systems-project.git

## How to use it
Firstly, it is necessary to clone the repository and change it to the corresponding directory
```
$ git clone https://github.com/AlejandroHoyo/distributed-systems-project.git
$ cd distributed-systems-project
```
Secondly, it is required to create a virtual environment and activate it
```
$ python3 -m venv .venv
$ source .venv/bin/activate

```
Then, it required to install all the dependencies from the `pyproject.toml` in the virtual environment. In order to do this it is required the following command

```
$ pip install .
```
If it is necessay to edit the code after the package installitation but without having to reinstall it again to test changes, the following commands may be required

```
$ python3 -m pip install --upgrade pip
$ python3 -m pip install -e .
```

Finally, you can run the service using the following command

```
./run_icestorm
./run_authentication_server

