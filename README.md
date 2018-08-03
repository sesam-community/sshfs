# SSHFS proxy

Proxy for reading and writing files over SSH using HTTP.

Also supports listing directory content as JSON entities. 

## Example System Config
```
{
  "_id": "my-ssh-server",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "HOSTNAME": "*hostname*",
      "USERNAME": "some_username",
      "PASSWORD": "some_password"
    },
    "image": "sesamcommunity/sshfs:latest",
    "port": 5000
  }
}
```

## [GET] single file
```
{
  "_id": "my-file",
  "type": "pipe",
  "source": {
    "type": "csv",
    "system": "my-ssh-server",
    "url": "/path/to/csv/file.csv",
  }
}
```

## [GET] file listing
```
{
  "_id": "my-directory",
  "type": "pipe",
  "source": {
    "type": "json",
    "system": "my-ssh-server",
    "url": "/path/to/directory",
  }
}
```

You can also add ```?relative=true``` if the path should be interpreted from the home directory of the ssh user.

Example output:

```
[
  {
    "url": "http://localhost:5000/Dockerfile",
    "_id": "Dockerfile"
  },
  {
    "url": "http://localhost:5000/LICENCE",
    "_id": "LICENCE"
  },
  {
    "url": "http://localhost:5000/README.md",
    "_id": "README.md"
  },
  {
    "url": "http://localhost:5000/service",
    "_id": "service"
  }
]
```

##### [POST] pipe config
```
{
  "_id": "my-output-file",
  "type": "pipe",
  "source": {
    "type": "dataset",
    "dataset": "some_dataset"
  },
  "sink": {
    "type": "json",
    "system": "my-ssh-server",
    "url": "/path/to/file.json"
  }
}
```
