package main

import (
	"io"
	"net"
	"os"
	"testing"
)

func TestConnection(t *testing.T) {
	// Simply check that the server is up and can
	// accept connections.
	conn, err := net.Dial("tcp", "localhost:8080")
	if err != nil {
		t.Error("could not connect to server: ", err)
	}
	defer conn.Close()
}

func TestPeerMessaging(t *testing.T) {
	_, err := net.Listen("tcp", "localhost:7000")
	if err != nil {
		t.Error("could not listen to localhost:7000: ", err)
	}

	rescueStdout := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	connectToPeer("8080", "peer_test", "7000")

	w.Close()
	out, _ := io.ReadAll(r)
	os.Stdout = rescueStdout

	if len(out) <= 0 {
		t.Error("No communication between peer1 and peer2")
	}
}
