<style scoped lang="less">
    .stream-card {
        width: 500px;
        display: block;
        background-color: lightyellow;
        float:left;
    }
</style>
<template>
    <card class="stream-card">
        <div class="stream-view">
            <h3>Stream : {{ stream.name }}</h3>
            <h5>({{ stream.url }})</h5>
            <img :id="stream.name" src="" width="450" height="300"></img>
        </div>
    </card>
</template>
<script>
export default {
    props : [ 'stream' ],
    data () {
        return {
            socket: null,
        }
    },
    mounted () {
        this.connectWebsocketServer();
        setInterval(this.forceUpdate, 10 * 60 * 1000);
    },
    methods: {
        connectWebsocketServer() {
            var ws = new WebSocket(this.stream.url.replace("http", "ws"));
            ws.binaryType = 'blob';
            console.log(this.stream.name);
            var img = document.getElementById(this.stream.name);
            img.onload = function() {
                URL.revokeObjectURL(this.src);
            };
            img.onended = function() {
                URL.revokeObjectURL(this.src);
            };

            ws.onopen = function(evt) {
                console.log("websocket onopen!");
            };
            ws.onclose = function(evt) {
                console.log("wesocket onclose!");
            };
            ws.onmessage = function(e) {
                URL.revokeObjectURL(img.src);
                img.src = URL.createObjectURL(e.data, {oneTimeOnly: true});
            }
            this.socket = ws;
        },
        forceUpdate() {
            console.log("Force Update");
            this.socket.close();
            location.reload();
        }
    }
}
</script>