import Vue from 'vue'
import api from './api'
import {helpers, api_endpoints} from '@/utils/hooks' 

export default {
    fetchProfile: function (){
        return new Promise ((resolve,reject) => {
            Vue.http.get(api.profile).then((response) => {
                resolve(response.body);
            },
            (error) => {
                reject(error);
            });
        });

    },
    fetchProposal: function(id){
        return new Promise ((resolve,reject) => {
            Vue.http.get(helpers.add_endpoint_json(api.proposals,id)).then((response) => {
                resolve(response.body);
            },
            (error) => {
                reject(error);
            });
        });
    },
    fetchCountries: function (){
        return new Promise ((resolve,reject) => {
            Vue.http.get(api.countries).then((response) => {
                resolve(response.body);
            },
            (error) => {
                reject(error);
            });
        });

    },
    fetchOrganisationPermissions: function(id){
        return new Promise ((resolve,reject) => {
            Vue.http.get(helpers.add_endpoint_json(api.my_organisations,id)).then((response) => {
                resolve(response.body);
            },
            (error) => {
                reject(error);
            });
        });
    },
    fetchOrganisation: function(id){
        // Guard clause to prevent API calls with an invalid ID.
        // If 'id' is null, undefined, 0, or an empty string, reject the promise immediately.
        if (!id) {
            return Promise.reject(new Error('An organisation ID is required to fetch data.'));
        }

        return new Promise ((resolve,reject) => {
            Vue.http.get(helpers.add_endpoint_json(api.organisations,id)).then((response) => {
                resolve(response.body);
            },
            (error) => {
                reject(error);
            });
        });
    },
    fetchOrganisationId: function(org_id) {
        return new Promise ((resolve,reject) => {
            Vue.http.get(api_endpoints.get_organisation_id(org_id)).then((response) => {
                resolve(response.body);
            },
            (error) => {
                reject(error);
            });
        });
    },
}
