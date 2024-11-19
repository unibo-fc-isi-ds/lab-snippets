package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"os"
	"strings"
	"time"
	"encoding/json"
)


const (
	CONN_TYPE = "tcp"

	CMD_PREFIX = "/"
	CMD_JOIN   = CMD_PREFIX + "join"
	CMD_DIAL   = CMD_PREFIX + "dial"
	CMD_INIT   = CMD_PREFIX + "init"
	CMD_CHATSEND   = CMD_PREFIX + "chatS"
	CMD_CHATRECEIVE   = CMD_PREFIX + "chatR"

	PURPLE_CLR = "\033[35m"
	CYAN_CLR = "\033[36m" 
	BLACK_CLR = "\033[1;30m"
	YELLOW_CLR = "\033[33m"
	GREEN_CLR = "\033[32m"
	RESET_CLR = "\033[0m"
)

type Client struct {
	name string
	chatRoom *ChatRoom
	incoming chan *Message
	outgoing chan string
	conn net.Conn
	reader *bufio.Reader
	writer *bufio.Writer
}

func NewClient(chatRoom *ChatRoom, conn net.Conn) *Client {
	client := &Client {
		name:     "",
		chatRoom: chatRoom,
		incoming: make(chan *Message, 1),
		outgoing: make(chan string),
		conn:     conn,
		reader:   nil,
		writer:   nil,
	}
	client.reader = bufio.NewReader(conn)
	client.writer = bufio.NewWriter(conn)
	client.Listen()
	return client
}

// Function called when connection closed
func (client *Client) Quit() {
	fmt.Println(PURPLE_CLR + client.name + " has left the chat" + RESET_CLR)
	delete(client.chatRoom.clients, client.conn.RemoteAddr().String())
	client.conn.Close()
}

// Reads and parse the string received, if it has some prefix than it does some function. if not, it prints it
func (client *Client) Read() {
	go func() {
		for message := range client.incoming {
			switch {
			default:
				mess := message.String()
				client.chatRoom.messages = append(client.chatRoom.messages, mess)
				fmt.Print(mess)
			// On client creation, i set his name
			case strings.HasPrefix(message.text, CMD_INIT):
				client.name = strings.TrimSpace(strings.TrimPrefix(message.text, CMD_INIT+" "))
			// On client creation, one peer sends the chat log to the new client
			case strings.HasPrefix(message.text, CMD_CHATSEND):
				port := strings.TrimSpace(strings.TrimPrefix(message.text, CMD_CHATSEND+" "))
				for _, x := range client.chatRoom.clients {

					if strings.HasSuffix(x.conn.RemoteAddr().String(), port) {
						mesStr, err := json.Marshal(x.chatRoom.messages)
						if err != nil {
							break
						}
						x.outgoing <- CMD_CHATRECEIVE + " " + string(mesStr) + "\n"
					}
				}
			// The new client receives the chat and prints it
			case strings.HasPrefix(message.text, CMD_CHATRECEIVE):
				messages := strings.TrimSpace(strings.TrimSuffix(strings.TrimPrefix(message.text, CMD_CHATRECEIVE+" "), "\n"))
				err := json.Unmarshal([]byte(messages), &client.chatRoom.messages)
				if err != nil {
					break
				}
				for _, x := range client.chatRoom.messages {
					fmt.Print(x)
				}
			// On new client join, a peer broadcasts to everyone his port
			case strings.HasPrefix(message.text, CMD_JOIN):
				fmt.Println(CYAN_CLR + strings.TrimSpace(strings.Split(message.text, "|")[1]) + " has joined the chat" + RESET_CLR)
				client.chatRoom.Broadcast(strings.TrimSpace(strings.TrimPrefix(message.text, CMD_JOIN+" ")) + "\n")
			// The rest of the peers receive the port and connects to it
			case strings.HasPrefix(message.text, CMD_DIAL):
				slice := strings.Split(message.text, "|")
				port := strings.TrimSpace(strings.TrimPrefix(slice[0], CMD_DIAL+" "))
				if client.chatRoom.connPort == port {
					break
				}
				fmt.Println(CYAN_CLR + slice[1] + " has joined the chat" + RESET_CLR)
				// i check if the client connecting is already present in my clients. if it is not, the i add it.
				for _, x := range client.chatRoom.clients {
					conn := x.conn.LocalAddr().String()
					presentPort := strings.Split(conn, ":")[1]
					if port != (":" + presentPort) {
						conn, err := net.Dial(CONN_TYPE, port)
						if err != nil {
							fmt.Println(err)
						}
						client := NewClient(x.chatRoom, conn)
						x.chatRoom.Join(client)
						break
					}
				}
			}
		}
	}()
}

// if a message is inserted in the outgoing field, than it is printed
func (client *Client) Write() {
	for message := range client.outgoing {
		_, err := client.writer.WriteString(message)
		if err != nil {
			client.Quit()
			fmt.Println(err)
			os.Exit(1)
		}
		err = client.writer.Flush()
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
	}
}

// Reads all incoming messages and put them in the incoming field.
func (client *Client)ClientRead(conn net.Conn) {
	reader := bufio.NewReader(conn)
	for {
		str, err := reader.ReadString('\n')
		if err != nil {
			client.Quit()
			return
		}
		message := NewMessage(time.Now(), client, strings.TrimSuffix(str, "\n"))
		client.incoming <- message
	}
}

// Reads from Stdin, and outputs to the socket.
func (client *Client)ClientWrite(conn net.Conn) {
	reader := bufio.NewReader(os.Stdin)
	client.chatRoom.Broadcast(CMD_INIT + " " + client.chatRoom.pointName)
	for {
		str, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
		str = strings.TrimPrefix(str, CMD_PREFIX)

		client.chatRoom.messages = append(
			client.chatRoom.messages, 
			PlainMessage(time.Now(), client.chatRoom.pointName, strings.TrimSuffix(str, "\n")))
		client.chatRoom.Broadcast(str)
	}
}

// starts all the go-routines
func (client *Client) Listen() {
	go client.Read()
	go client.Write()
	go client.ClientRead(client.conn)
	go client.ClientWrite(client.conn)
}

type ChatRoom struct {
	pointName string
	clients  map[string]*Client
	connPort string
	messages []string
}

func NewChatRoom(connPort string) *ChatRoom {

	chatRoom := &ChatRoom{
		pointName: "",
		clients: make(map[string]*Client),
		messages: make([]string, 0),
		connPort: connPort,
	}

	return chatRoom
}

// add client to the chatroom
func (chatRoom *ChatRoom) Join(client *Client) {
	chatRoom.clients[client.conn.RemoteAddr().String()] = client
}

// sends the message to all the clients connected
func (chatRoom *ChatRoom) Broadcast(message string) {
	for _, client := range chatRoom.clients {
		client.outgoing <- message
	}
}

type Message struct {
	time time.Time
	client *Client
	text string
}

func NewMessage(time time.Time, client *Client, text string) *Message {
	return &Message{
		time:   time,
		client: client,
		text:   text,
	}
}

// format the string to send
func (message *Message) String() string {
	return fmt.Sprintf(BLACK_CLR + "%s - %s:" + GREEN_CLR + " %s\n" + RESET_CLR, 
		message.time.Format(time.Kitchen), message.client.name, message.text)
}

// format the string to send
func PlainMessage(messTime time.Time, name string, text string) string {
	return fmt.Sprintf(BLACK_CLR + "%s - %s:" + GREEN_CLR + " %s\n" + RESET_CLR, 
		messTime.Format(time.Kitchen), strings.TrimSpace(strings.TrimSuffix(name, "\n")), text)
}

func main() {
	// Checks if the params are correct
	if len(os.Args) <= 1 {
		log.Println("required server port as parameter 1 and port to connect to as parameter 2(optional)")
		os.Exit(1)
	}

	// Takes connection port and creates the listener, assuming the connection port given is correct (:xxxx)
	connPort := os.Args[1]
	chatRoom := NewChatRoom(connPort)

	listener, err := net.Listen(CONN_TYPE, "localhost" + connPort)
	if err != nil {
		log.Println("Error", err)
		os.Exit(1)
	}
	defer listener.Close()
	fmt.Println(PURPLE_CLR +"listening on port", "localhost" + connPort + RESET_CLR)
	
	reader := bufio.NewReader(os.Stdin)
	
	// Before doing anything i wait for the user name 
	fmt.Print(GREEN_CLR + "Enter name: " + RESET_CLR)
	text, err := reader.ReadString('\n')
	if err != nil {
		log.Println(err)
	}
	chatRoom.pointName = text

	// If the user putted a server to connect to i connect to it and broadcast to everyone the port, to let everyone know there is a new member
	if len(os.Args) >= 3 {

		conn, err := net.Dial(CONN_TYPE, os.Args[2])
		if err != nil {
			fmt.Println(err)
		}

		client := NewClient(chatRoom, conn)
		chatRoom.Join(client)
		client.outgoing <- CMD_JOIN + " "  + CMD_DIAL + " " + connPort + "|" + strings.TrimSuffix(chatRoom.pointName, "\n") + "\n"
		client.outgoing <- CMD_CHATSEND + " " + conn.LocalAddr().String() + "\n"
	}
	// Waits for a new client to connect.
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Println("Error: ", err)
			continue
		}
		client := NewClient(chatRoom, conn)
		chatRoom.Join(client)
	}
}