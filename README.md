# hydra-onlineview

### introduction
Objective of the project is to provide relevant information about the illegal sale of drugs in real-time. The service can be configured to work with any distribution region.

### Notes
 - All products without the specified metro station will be ignored
 - Preorder section will be ignored too
 - Information is updated constantly
 - Information is actual only for the last 24 hours
 
### Installation
hydra-onlineview requires [Docker](https://www.docker.com/) v1.9+ to run.
basic configuration settings is in .env file
```sh
$ cd hydra-onlineview
$ docker-compose build
```
to run
```sh
$ docker-compose up -d
```
main page(by default)
```sh
http://127.0.0.1/statistics
```
### Api
- Get all categories
```sh
GET /getcategories
```
- Get all stowages by category by last 24 hours
```sh
GET /view/<category>
```
- Get captcha image as b64 string or 0 if captcha recognition dont needed
```
GET /getcaptcha
```
- Solve captcha
```
POST /solve/
      answer = <recognited text>
```
