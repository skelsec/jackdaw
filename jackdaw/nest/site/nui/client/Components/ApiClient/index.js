'use strict';

import React from 'react';
import { connect } from 'react-redux';

import BackendService from '../../Services/BackendService';

const Store = require('../../Store');
import * as actions from '../../Store/actions';

class ApiClient extends React.Component {

    notifyUser = (message) => {
        if ([undefined, null].includes(message)) return false;
        Store.dispatch(actions.notifyUser(message));
    }

    isResponseOk = async(result, message) => {
        if ([undefined, null].includes(result)) {
            return false;
        }
        if (result.status == 200) {
            return true;
        }
        this.notifyUser({
            severity: 'warning',
            "message": message
        });
        return false;
    }

    apiFetch = async(url, error) => {
        const result = await BackendService.get(url);
        const message = [undefined, null].includes(error) ? 'Operation failed' : error;
        if (!await this.isResponseOk(result, message)) return false;
        return result;
    }

    apiCreate = async(url, data, error) => {
        const result = await BackendService.post(url, data);
        const message = [undefined, null].includes(error) ? 'Operation failed' : error;
        if (!await this.isResponseOk(result, message)) return false;
        return result;
    }

    apiUpdate = async(url, data, error) => {
        const result = await BackendService.update(url, data);
        const message = [undefined, null].includes(error) ? 'Operation failed' : error;
        if (!await this.isResponseOk(result, message)) return false;
        return result;
    }

    apiRemove = async(url, error) => {
        const result = await BackendService.remove(url);
        const message = [undefined, null].includes(error) ? 'Operation failed' : error;
        if (!await this.isResponseOk(result, message)) return false;
        return result;
    }

}

export default ApiClient;
