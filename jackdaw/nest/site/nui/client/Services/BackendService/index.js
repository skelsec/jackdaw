'use strict';

const https = require('https');
const axios = require('axios');

class BackendService {

    constructor() {
        this.agent = new https.Agent({  
            rejectUnauthorized: false
        });

        axios.interceptors.response.use(function (response) {
            return response;
        }, function (error) {
            return error.response;
        });

    }

    prepareHttpHeaders = () => {
        var httpHeaders = {};
        // To add any headers...
        return httpHeaders;
    }

    get = async(url) => {
        try {
            return await axios.get(url, {
                httpsAgent: this.agent
            });
        } catch (e) {
            console.log(e); // TODO
            return null;
        }
    }

    remove = async(url) => {
        try {
            return await axios.delete(url, {
                httpsAgent: this.agent,
                headers: this.prepareHttpHeaders()
            });
        } catch (e) {
            console.log(e); // TODO
            return null;
        }
    }

    post = async(url, data) => {
        try {
            return await axios.post(url, data, {
                httpsAgent: this.agent,
                headers: this.prepareHttpHeaders()
            });
        } catch (e) {
            console.log(e); // TODO
            return null;
        }
    }

    update = async(url, data) => {
        try {
            return await axios.put(url, data, {
                httpsAgent: this.agent,
                headers: this.prepareHttpHeaders()
            });
        } catch (e) {
            console.log(e); // TODO
            return null;
        }
    }
}

module.exports = new BackendService();
