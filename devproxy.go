//
// Copyright 2016 Cluster Labs, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

package main

import (
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
)

type SingleHostReverseProxyWithCORS struct {
	proxy *httputil.ReverseProxy
}

func NewSingleHostReverseProxyWithCORS(url *url.URL) *SingleHostReverseProxyWithCORS {
	r := SingleHostReverseProxyWithCORS{}
	// NOTE: Not using the bottleneck here because App Engine requests to itself.
	r.proxy = httputil.NewSingleHostReverseProxy(url)
	return &r
}

func (r *SingleHostReverseProxyWithCORS) ServeHTTP(rw http.ResponseWriter, req *http.Request) {
	rw.Header().Set("Access-Control-Allow-Origin", "*")
	r.proxy.ServeHTTP(rw, req)
}

func main() {
	if len(os.Args) != 3 {
		log.Fatal("Usage: go run ./devproxy.go [listen host and port] [to host and port]")
	}

	hostAndPort := os.Args[1]
	proxyHost := os.Args[2]

	proxy := NewSingleHostReverseProxyWithCORS(&url.URL{Scheme: "http", Host: proxyHost, Path: "/"})
	server := &http.Server{
		Addr:    hostAndPort,
		Handler: proxy,
	}

	log.Print("Dev proxy listening on: ", hostAndPort, " redirecting to: ", proxyHost)
	err := server.ListenAndServe()
	if err != nil {
		log.Fatal(err)
	}
}
