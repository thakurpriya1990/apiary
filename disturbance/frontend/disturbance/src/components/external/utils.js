// import Vue from 'vue'
import api from './api'
import {helpers, api_endpoints} from '@/utils/hooks' 

export default {
    fetchProfile: function (){
        return new Promise ((resolve,reject) => {
            fetch(api.profile).then(
                async (response) => {
                    if (!response.ok) {
                        return await response.json().then(err => { throw err });
                    }
                    const data = await response.json();
                    resolve(data);
                }).catch(error => {
                    reject(error);
                });
        });

    },
    fetchProposal: function(id){
        return new Promise ((resolve,reject) => {
            fetch(helpers.add_endpoint_json(api.proposals,id)).then(
                async (response) => {
                    if (!response.ok) {
                        return await response.json().then(err => { throw err });
                    }
                    const data = await response.json();
                    resolve(data);
                }).catch(error => {
                    reject(error);
                });
        });
    },
    fetchCountries: function (){
        return new Promise ((resolve,reject) => {
            fetch(api.countries).then(
                async (response) => {
                    const data = await response.json();
                    resolve(data);
                }).catch(error => {
                    reject(error);
                });
        });

    },
    fetchOrganisationPermissions: async function(id){
        const response = await fetch(helpers.add_endpoint_json(api.my_organisations, id));
        if (!response.ok) {
            const errorData = await response.json();
            throw errorData;
        }
        return await response.json();
    },
    fetchOrganisation: async function(id){
        // Guard clause to prevent API calls with an invalid ID.
        // If 'id' is null, undefined, 0, or an empty string, reject the promise immediately.
        if (!id) {
            return Promise.reject(new Error('An organisation ID is required to fetch data.'));
        }

        const response = await fetch(helpers.add_endpoint_json(api.organisations, id));
        if (!response.ok) {
            const errorData = await response.json();
            throw errorData;
        }
        return await response.json();
    },
    fetchOrganisationId: async function(org_id) {
        const response = await fetch(api_endpoints.get_organisation_id(org_id));
        if (!response.ok) {
            const errorData = await response.json();
            throw errorData;
        }
        return await response.json();
    },
}
