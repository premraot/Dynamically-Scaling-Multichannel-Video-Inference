<style scoped lang="less">
    .layout{
        width: 100%;
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        text-align: center;
    }
    .input-server {
        width: 50%;
        left: 25%;
        position: relative;
    }
    .stream-area {
        left: 20px;
        right: 20px;
        top: 20px;
        position: relative;
    }
</style>
<template>
    <div class="layout">
        <div>
            <h1>Edge Server Inference Pipeline</h1>
        </div>
        <div class="stream-area">
            <StreamView v-for="stream in streams" v-bind:key="stream.name" v-bind:stream="stream" ></StreamView>
        </div>
    </div>
</template>
<script>
    import axios from "axios";
    import StreamView from "../components/StreamView.vue"

    export default {
        components: {
            StreamView
        },
        data() {
            return {
                api_server_url: window.location.href + "api",
                ws_server_host: window.location.hostname, // default value for websocket
                ws_server_port: 31611,                    // default value for websocket
                streams: [],
                stream_names: []
            }
        },
        mounted () {
            console.log("index.vue mounted.");
            setInterval(this.updateStreams, 1000);
        },
        methods: {
            updateStreams () {
                axios({ method: "GET", "url": this.api_server_url + "/streams"}).then(result => {
                    // add new stream if not exist
                    for (var index=0; index < result.data.streams.length; index++) {
                        var stream_name = result.data.streams[index];
                        if (this.stream_names.indexOf(stream_name) < 0) {
                            console.log("add stream: " + stream_name)
                            this.stream_names.push(stream_name);
                            this.streams.push({
                                "name": stream_name,
                                "url": "ws://" + this.ws_server_host + ":" + this.ws_server_port + "/" + stream_name
                                })
                        }
                    }
                    // remove stopped stream
                    for (var index=0; index < this.stream_names.length; index++) {
                        if (result.data.streams.indexOf(this.stream_names[index]) < 0) {
                            console.log("remove stream: " + this.stream_names[index])
                            this.streams.splice(index, 1);
                            this.stream_names.splice(index, 1);
                        }
                    }
                }, error => {
                    console.error(error);
                    this.$Message.error('Fail to call restful API: ' + this.api_server_url + "/streams");
                });
            },
        },

    }
</script>