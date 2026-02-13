<template lang="html">
    <div>
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
            <div class="container-fluid">
                <div class="row">

                    <div class="form-group"><div class="row mb-3">
                        <label class="col-sm-4 col-form-label">Period From</label>
                        <div class="col-sm-8">
                            <div class="input-group date" ref="periodFromDatePicker">
                                <input type="date" class="form-control" name="period_from_input_element" placeholder="DD/MM/YYYY" v-model="on_site_information.period_from" :max="on_site_information.period_to">
                            </div>
                        </div>
                    </div></div>

                    <div class="form-group"><div class="row mb-3">
                        <label class="col-sm-4 col-form-label">Period To</label>
                        <div class="col-sm-8">
                            <div class="input-group date" ref="periodToDatePicker">
                                <input type="date" class="form-control" name="period_to_input_element" placeholder="DD/MM/YYYY" v-model="on_site_information.period_to" :min="on_site_information.period_from">
                            </div>
                        </div>
                    </div></div>

                    <div class="form-group"><div class="row mb-3">
                        <label class="col-sm-4 col-form-label">Site</label>
                        <div class="col-sm-8">
                            <select class="form-select" v-model="on_site_information.apiary_site_id">
                                <option value=""></option>
                                <option v-for="site in apiary_sites_options" :value="site.id" :key="site.id">
                                    Site: {{ site.id }}
                                </option>
                            </select>
                        </div>
                    </div></div>

                    <div class="form-group"><div class="row mb-3">
                        <label class="col-sm-4 col-form-label">The proposed location of the hives</label>
                        <div class="col-sm-8">
                            <textarea class="form-control" v-model="on_site_information.hives_loc"/>
                        </div>
                    </div></div>

                    <div class="form-group"><div class="row mb-3">
                        <label class="col-sm-4 col-form-label">Number of hives proposed to be placed on the site</label>
                        <div class="col-sm-8">
                            <input type='number' value="0" class="form-control" v-model="on_site_information.hives_num"/>
                        </div>
                    </div></div>

                    <div class="form-group"><div class="row mb-3">
                        <label class="col-sm-4 col-form-label">The names of the people who are expected to be entering the site for apiary purposes</label>
                        <div class="col-sm-8">
                            <textarea class="form-control" v-model="on_site_information.people_names"/>
                        </div>
                    </div></div>

                    <div class="form-group"><div class="row mb-3">
                        <label class="col-sm-4 col-form-label">Flora targeted</label>
                        <div class="col-sm-8">
                            <textarea class="form-control" v-model="on_site_information.flora"/>
                        </div>
                    </div></div>


                    <div class="form-group"><div class="row mb-3">
                        <label class="col-sm-4 col-form-label">Comments</label>
                        <div class="col-sm-8">
                            <textarea class="form-control" v-model="on_site_information.comments"/>
                        </div>
                    </div></div>

                </div>
            </div>
            <template #footer>
                <div v-if="errorResponse" class="form-group">
                    <div class="row">
                        <div class="col-sm-12">
                            <strong>
                                <span style="white-space: pre;" v-html="errorResponse"></span>
                            </strong>
                        </div>
                    </div>
                </div>
                <button type="button" v-if="processingDetails" disabled class="btn btn-primary" @click="ok"><i class="fa fa-spinner fa-spin"></i> Adding</button>
                <button type="button" v-else class="btn btn-primary" @click="ok">Ok</button>
                <button type="button" class="btn btn-secondary" @click="cancel">Cancel</button>
            </template>
        </modal>
    </div>
</template>

<script>
    import modal from '@vue-utils/bootstrap-modal.vue';
    // import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";

    export default {
        name: "OnSiteInformationAdd",
        data: function() {
            return {
                processingDetails: false,
                isModalOpen: false,
                errorResponse: '',
                apiary_sites_options: [],
            }
        },
        components: {
          modal,
        },
        props:{
            on_site_information: {
                type: Object,
            },
            approval_id: {
                type: Number,
                required: true,
                default: 0,
            },
        },
        watch:{
            isModalOpen: function() {
            }
        },
        computed: {
            modalTitle: function() {
                return 'Add on site info'
            },
        },
        created: function() {
            this.loadApiarySites()
        },
        methods: {
            openMe: function () {
                this.isModalOpen = true
            },
            loadApiarySites: function(){
                fetch('/api/approvals/' + this.approval_id + '/apiary_site/')
                .then(async (response)=>{
                    if (!response.ok) { return response.json().then(err => { throw err }); }
                    const data = await response.json();
                    this.apiary_sites_options = data
                }).catch((error) => {
                    console.log(error);
                });
            },
            ok: async function () {
                try {
                    this.processingDetails = true;

                    // Update django database
                    const response = await this.sendData();
                    console.log('Response from server:', response);
                    // Inform the parent component that the database has been updated
                    // so that the parent component can update a table
                    this.$emit('on_site_information_added');

                    this.close();
                } catch (err){
                    this.processError(err);
                } finally {
                    this.processingDetails = false;
                }
            },
            processError: async function(err) {
                let errorText = '';
                if (err.body.non_field_errors) {
                    // When non field errors raised
                    for (let i=0; i<err.body.non_field_errors.length; i++){
                        errorText += err.body.non_field_errors[i] + '<br />';
                    }
                } else if(Array.isArray(err.body)) {
                    // When general errors raised
                    for (let i=0; i<err.body.length; i++){
                        errorText += err.body[i] + '<br />';
                    }
                } else {
                    // When field errors raised
                    for (let field_name in err.body){
                        if (Object.prototype.hasOwnProperty.call(err.body, field_name)) {
                            errorText += field_name + ': ';
                            for (let j=0; j<err.body[field_name].length; j++){
                                errorText += err.body[field_name][j] + '<br />';
                            }
                        }
                    }
                }
                this.errorResponse = errorText;
            },
            cancel: async function() {
                this.isModalOpen = false;
                this.close();
            },
            close: function () {
                this.isModalOpen = false;
            },
            sendData: async function () {
                let base_url = '/api/on_site_information/'
                let payload = {}
                Object.assign(payload, this.on_site_information);

                payload.approval_id = this.approval_id

                let res = '';
                try {
                    if (this.on_site_information.id) {
                        // Update existing on-site-information
                        res = await fetch(base_url + this.on_site_information.id + '/', {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(payload)
                        });
                    } else {
                        // Create new on-site-information
                        res = await fetch(base_url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(payload)
                        });
                    }

                    if (!res.ok) {
                        const errorText = await res.text();
                        throw new Error(`Request failed with status ${res.status}: ${errorText}`);
                    }

                    const data = await res.json();
                    return data; // Return parsed JSON instead of raw response

                } catch (error) {
                    console.error('Error occurred:', error.message);
                    return { error: error.message }; // Return an error object for handling in UI
                }

            },
        },
    }
</script>

<style>

</style>
