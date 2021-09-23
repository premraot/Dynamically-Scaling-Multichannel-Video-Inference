const routers = [
    {
        path: '/',
        meta: {
            title: 'Clear Linux Elastic Inference Demo'
        },
        component: (resolve) => require(['./views/index.vue'], resolve)
    }
];
export default routers;