# didactic_p2p_tcp_groupchat
Simple university project for a peer to peer tcp group chat, with no CS structure

## Run the application

```shell
go run . <hosting-port> <peer1-port> ...
```
Otherwise we can use the exe file given

## Build the application
```shell
go build
```

## Test the application
To test the application we assume that there is a peer running at localhost:8080

```shell
go run . 8080
```

```shell
go test
```

## Go installation
To install go you can visit the [Download & Install](https://go.dev/doc/install) go documentation page
