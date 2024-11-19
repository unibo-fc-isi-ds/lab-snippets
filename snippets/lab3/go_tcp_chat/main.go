package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"strings"
	"sync"
)

var peers = make(map[string]net.Conn)
var addrToUsername = make(map[string]string)
var remoteAddressTable = make(map[string]string)
var mutex sync.Mutex
var reset = "\033[0m" // reset to default terminal strings color
var blue = "\033[34m" // blue string color on terminal

// check if the connection is from a peer
func isPeer(conn net.Conn) bool {
	_, ok := remoteAddressTable[conn.RemoteAddr().String()]
	return !ok
}

// function to handle the connection, the peer will start listening for data messages
// when the connection will be interrupter the for loop will break
func handleConnection(conn net.Conn) {
	defer conn.Close()
	peerAddr := conn.RemoteAddr().String()

	// start scanning on the connection for messages
	scanner := bufio.NewScanner(conn)
	for scanner.Scan() {
		message := scanner.Text()
		fmt.Printf("%s\n", message)
	}

	// Remove peer on disconnect
	mutex.Lock()
	fmt.Printf("%sPeer %s left the chat\n%s", blue, remoteAddressTable[peerAddr], reset)
	delete(peers, peerAddr)
	delete(addrToUsername, peerAddr)
	mutex.Unlock()
}

// function to broadcast the message to all other peers
func broadcastMessage(message string, sender string) {
	mutex.Lock()
	defer mutex.Unlock()
	for addr, conn := range peers {
		if addr != sender {
			fmt.Fprintf(conn, "%s: %s\n", sender, message)
		}
	}
}

// function to connect to a peer
func connectToPeer(addr string, username string, port string) {
	conn, err := net.Dial("tcp", "localhost:"+addr)
	if err != nil {
		fmt.Printf("%sFailed to connect to %s: %v\n%s", blue, addr, err, reset)
		return
	}
	// Scanner for the presentation message from the peer we want to connect
	getPresentationMessage(conn)
	sendPresentationMessage(conn, username, port)
	fmt.Printf("%s%s was already in the chat!\n%s", blue, addrToUsername[addr], reset)
	go handleConnection(conn)
}

// function to receive the init message where the peer send his basic informations
func getPresentationMessage(conn net.Conn) {
	scanner := bufio.NewScanner(conn)
	for scanner.Scan() {
		message := scanner.Text()
		if message[0] == '>' {
			senderInformation := strings.Split(message[1:], ":")
			mutex.Lock()
			addrToUsername[senderInformation[1]] = senderInformation[0]
			peers[senderInformation[1]] = conn
			remoteAddressTable[conn.RemoteAddr().String()] = senderInformation[0]
			mutex.Unlock()
			break
		}
	}
}

// function to send the init message with all useful informations
func sendPresentationMessage(conn net.Conn, username string, port string) {
	fmt.Fprintf(conn, ">%s:%s\n", username, port)
}

// function to read an input from the console and broadcast it to all the connected peers
func readInput(username string) {
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		message := scanner.Text()
		// Send this message to all connected peers
		broadcastMessage(message, username)
	}
}

func main() {
	if len(os.Args) < 1 {
		fmt.Println("Usage: go run main.go [port] [peer1] [peer2] ...")
		return
	}

	// Read the username for the user
	username := ""
	fmt.Printf("Enter your username : ")
	scanner := bufio.NewReader(os.Stdin)
	username, err := scanner.ReadString('\n')
	if err != nil {
		panic(err)
	}
	username = username[:(len(username) - 2)] // remove the \n at the end of the string
	fmt.Printf("%sWelcome %s!\n%s", blue, username, reset)

	port := os.Args[1]
	listener, err := net.Listen("tcp", "localhost:"+port)
	if err != nil {
		fmt.Printf("%sFailed to bind to port %s: %v\n%s", blue, port, err, reset)
		return
	}
	defer listener.Close()
	fmt.Printf("%sListening on port %s\n%s", blue, port, reset)

	if len(os.Args) > 1 {
		// Connect to initial peers
		for _, peerAddr := range os.Args[2:] {
			go connectToPeer(peerAddr, username, port)
		}
	}

	// Start a goroutine for reading user input
	go readInput(username)

	// Accept incoming connections
	for {
		conn, err := listener.Accept()
		if err != nil {
			fmt.Printf("%sFailed to accept connection: %s\n%s", blue, err, reset)
			continue
		}
		peerAddr := conn.RemoteAddr().String()
		sendPresentationMessage(conn, username, port)
		getPresentationMessage(conn)
		fmt.Printf("%sPeer %s join the chat!\n%s", blue, remoteAddressTable[peerAddr], reset)
		go handleConnection(conn)
	}
}
