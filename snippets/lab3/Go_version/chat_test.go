package main

import (
	"strings"
	"testing"
	"time"
)

func TestNewMessage(t *testing.T) {
	client := &Client{name: "TestUser"}
	now := time.Now()
	msg := NewMessage(now, client, "Hello, World!")

	if msg.text != "Hello, World!" {
		t.Errorf("Expected message text 'Hello, World!', got %s", msg.text)
	}

	if msg.client.name != "TestUser" {
		t.Errorf("Expected client name 'TestUser', got %s", msg.client.name)
	}
}

func TestMessageString(t *testing.T) {
	client := &Client{name: "TestUser"}
	now := time.Date(2024, 11, 18, 15, 30, 0, 0, time.UTC)
	msg := NewMessage(now, client, "Hello, World!")

	expected := "3:30PM - TestUser: Hello, World\n"
	result := msg.String()

	if !strings.Contains(result, "TestUser") || !strings.Contains(result, "Hello, World") {
		t.Errorf("Expected formatted message '%s', got '%s'", expected, result)
	}
}

func TestBroadcast(t *testing.T) {
	chatRoom := NewChatRoom(":12345")
	client1 := &Client{name: "Client1", outgoing: make(chan string, 1)}
	client2 := &Client{name: "Client2", outgoing: make(chan string, 1)}

	chatRoom.clients["1"] = client1
	chatRoom.clients["2"] = client2

	message := "Hello, Clients!"
	chatRoom.Broadcast(message)

	select {
	case msg := <-client1.outgoing:
		if msg != message {
			t.Errorf("Expected '%s', got '%s'", message, msg)
		}
	default:
		t.Error("Client1 did not receive broadcast message")
	}

	select {
	case msg := <-client2.outgoing:
		if msg != message {
			t.Errorf("Expected '%s', got '%s'", message, msg)
		}
	default:
		t.Error("Client2 did not receive broadcast message")
	}
}

func TestPlainMessage(t *testing.T) {
	now := time.Date(2024, 11, 18, 15, 30, 0, 0, time.UTC)
	message := PlainMessage(now, "User", "Test Message")

	expected := "3:30PM - User: Test Message\n"
	if !strings.Contains(message, "User") || !strings.Contains(message, "Test Message") {
		t.Errorf("Expected formatted message '%s', got '%s'", expected, message)
	}
}

func TestClientRead(t *testing.T) {
	chatRoom := NewChatRoom(":12345")
	client := &Client{
		name:     "TestClient",
		chatRoom: chatRoom,
		incoming: make(chan *Message, 1),
	}

	now := time.Now()
	client.incoming <- NewMessage(now, client, "Hello, Read Test!")

	go client.Read()

	time.Sleep(100 * time.Millisecond)

	if len(chatRoom.messages) != 1 || !strings.Contains(chatRoom.messages[0], "Hello, Read Test!") {
		t.Errorf("Expected message to be processed and stored in chatRoom.messages")
	}
}