let util = {

};
util.title = function (title) {
    title = title ? title + ' - Home' : 'Clear Linux Elastic Inference Demo';
    window.document.title = title;
};

export default util;