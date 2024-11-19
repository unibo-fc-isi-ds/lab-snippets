# didactic_p2p_tcp_groupchat
Simple university project for a peer to peer tcp group chat in GoLang, with no CS structure. The project consist in a main.go file, following the idea of Go, the project is quite simple, no useless struct and no overcomplicated stuff. \
The program take as arguments the port where host the peer, and $n$ ports where are located the other peers. \
The key concept is quite simple, the main peer will connect to all others peer and start to listen to aacept all incoming connections, this functions will be different goroutines, to allow parallelism and concurrency. \
After connect to others peers a goroutine will be started to receive and tramit data with the peers on a TCP connection (one per peer)

Key components are the maps and the mutex, in the first one the peer can find the address and connection where to communicate with connected peers, and the second one are needed to share resources between all goroutines. 

### Workflow
1. Setup:
    The user specifies a port to listen on and optionally provides peer addresses to connect to.
    The program asks for the user's username.
2. Listening and Connecting:
    Starts listening on the specified port.
    Attempts to connect to the provided peers (if any).
3. Chat Functionality:
    For every incoming connection:
    Exchanges usernames with the peer.
    Adds the peer to the peers map.
    Messages typed by the user are broadcast to all connected peers.
    Messages from peers are printed to the console.
4. Disconnect Handling:
    Cleans up resources (like removing the peer from maps) when a peer disconnects.



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
