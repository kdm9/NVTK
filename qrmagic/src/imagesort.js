import Vue from 'vue/dist/vue.js';
import axios from 'axios';
import axiosRetry from 'axios-retry';
import axiosRateLimit from 'axios-rate-limit';
import { quote } from 'shell-quote';

/*
import { Reader, Writer } from '@transcend-io/conflux';
import streamSaver from 'streamsaver';
import { ReadableStream,  WritableStream } from "web-streams-polyfill/ponyfill";
streamSaver.ReadableStream = ReadableStream;
streamSaver.WritableStream = WritableStream;
*/

axios.default.timeout = 10000;
axiosRetry(axios, { retries: 4, retryDelay: axiosRetry.exponentialDelay });
axiosRateLimit(axios, {maxRPS: 1})
 
const MAX_REQUESTS_COUNT = 5
const INTERVAL_MS = 10
let PENDING_REQUESTS = 0

axios.interceptors.request.use(function (config) {
	  return new Promise((resolve, reject) => {
		      let interval = setInterval(() => {
				    if (PENDING_REQUESTS < MAX_REQUESTS_COUNT) {
						    PENDING_REQUESTS++
						    clearInterval(interval)
						    resolve(config)
						  } 
				  }, INTERVAL_MS)
		    })
})

axios.interceptors.response.use(function (response) {
	  PENDING_REQUESTS = Math.max(0, PENDING_REQUESTS - 1)
	  return Promise.resolve(response)
}, function (error) {
	  PENDING_REQUESTS = Math.max(0, PENDING_REQUESTS - 1)
	  return Promise.reject(error)
})


function readFile(file){
  return new Promise((resolve, reject) => {
    var fr = new FileReader();  
    fr.onload = () => {
      resolve(fr.result )
    };
    fr.onerror = reject;
    fr.readAsDataURL(file);
  });
}

var vm = new Vue({
    el: "#vf",
    data: {
        persistIDForSecs: 30,
        images: [],
        progress: false,
        zoomImg: false,
        hideFilled: false,
        showconfig: false,
        qr_sep: "_",
        reverse_sort: false,
    },
    methods: {
        async onImageSelect(e) {
            var files = e.target.files || e.dataTransfer.files;
            if (!files.length) return;
            this.progress = {done: 0, total: files.length};
            for (let [i, file] of Object.entries(files)) {
                var content = await readFile(file);
                var apidata = {filename: file.name, content: content};
                axios({method: 'post', url: '/api/scan-image', data: apidata})
                .then(function(req) {
                    if (req.status > 299) console.log(req);
                    const d = req.data;
                    if (d.qrcodes) {
                        if (vm.$data.reverse_sort) {
                            d.qrcodes.sort().reverse();
                        } else {
                            d.qrcodes.sort();
                        }
                    }
                    const id = d.qrcodes ? d.qrcodes.join(vm.$data.qr_sep) : "";
                    const dtobj = d.datetime ? new Date(d.datetime): undefined;
                    var data = {
                        id: id,
                        lat: d.lat,
                        lng: d.lng,
                        alt: d.alt,
                        datetime: dtobj,
                        datestr: dtobj ? dtobj.toISOString() : "",
                        image: d.midsize,
                        fileobj: file,
                        filename: file.name,
                        qrcodes: d.qrcodes,
                    };
                    vm.$data.progress.done += 1;
                    vm.$data.images.push(data);
                    if (vm.$data.progress.done == vm.$data.progress.total) {
                        vm.$data.images.sort((a1, a2) => {return a1.datetime - a2.datetime;})
                    }
                }).catch(function(err) {
                    console.log(err);
                    vm.$data.progress.done += 1;
		});
            }
        },
        async getRenamedZip() {
            alert("Not implemented");
            /*const { readable, writable } = new Writer();
            const writer = writable.getWriter();
            const fileStream = streamSaver.createWriteStream('renamed_images.zip');
            console.log(fileStream);
            for (let i in this.images) {
                const img = this.images[i];
                let filename = img.filename;
                if (img.id != "") {
                    filename = `/${img.id}/${img.filename}`;
                }
                writer.write(filename, img.fileobj);
            }
            readable.pipeTo(fileStream);
            writer.close();*/
        },
        async getRenamerScript() {
            let script = ['relocate() { mkdir -p "$(dirname "$2")"; mv "$1" "$2";}', ];
            for (let i in this.images) {
                const img = this.images[i];
                if (img.id != "") {
                    script.push(quote(["relocate",  img.filename, `${img.id}/${img.filename}`]));
                }
            }
            // Download script
            var element = document.createElement('a');
            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(script.join("\n")));
            element.setAttribute('download', "rename.sh");
            element.style.display = 'none';
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
        },
        autofillAllIDs() {
            for (let i in this.images) {
                this.idFromPreviousIfEmpty(i);
            }
        },
        removeImage(index) {
            this.images.splice(index, 1);
        },
        idFromPreviousIfEmpty(index) {
            const id = this.images[index].id;
            if (id == "" && index > 1) {
                const secSinceLast = (this.images[index].datetime - this.images[index-1].datetime)/1000;
                if (secSinceLast < this.persistIDForSecs) {
                    this.images[index].id = this.images[index-1].id;
                }
            }
        },
        setZoomImage(image) {
            if (this.zoomImg == image.image) {
                this.zoomImg = false;
            } else {
                this.zoomImg = image.image;
            }
        },
        killZoomImage() {
            this.zoomImg = false;
        }
    }
});
