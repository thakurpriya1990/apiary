<template>
    <div class="container" id="userInfo">
        <div class="row">
            <div class="col-sm-12">
                <FormSection
                    :form-collapse="false"
                    label="Organisations"
                    subtitle="Link to the Organisations you are an employee of and for which you are managing licences"
                >
                    <div class="panel panel-default">
                      <form class="form-horizontal" name="orgForm" method="post">
                          <div class="form-group">
                            <label for="" class="col-sm-5 control-label">Do you manage licences on behalf of an organisation?</label>
                            <div class="col-sm-4">
                                 <label class="radio-inline">
                                  <input :disabled="hasOrgs" type="radio" name="behalf_of_org" v-model="managesOrg" value="No" > No
                                </label>
                                <label class="radio-inline">
                                  <input type="radio" name="behalf_of_org" v-model="managesOrg" value="Yes"> Yes
                                </label>
                                 <label class="radio-inline">
                                  <input type="radio" name="behalf_of_org" v-model="managesOrg" value="Consultant"> Yes, as a consultant
                                </label>
                            </div>
                            <div v-if="managesOrg=='Yes'">
                                <div class="col-sm-3">
                                    <button class="btn btn-primary" v-if="hasOrgs && !addingCompany" @click.prevent="addCompany()">Add Another Organisation</button>
                                </div>
                            </div>
                          </div>
                          <div v-for="org in current_user.wildlifecompliance_organisations" v-bind:key="org.id">
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >Organisation</label>
                                <div class="col-sm-3"> 
                                    <input type="text" disabled class="form-control" name="organisation" v-model="org.name" placeholder="">
                                </div>
                                <label for="" class="col-sm-1 control-label" >ABN/ACN</label>
                                <div class="col-sm-3"> 
                                    <input type="text" disabled class="form-control" name="organisation" v-model="org.abn" placeholder="">
                                </div>
                                <a style="cursor:pointer;text-decoration:none;" @click.prevent="unlinkUser(org)"><i class="fa fa-chain-broken fa-2x" ></i>&nbsp;Unlink</a>
                              </div>
                          </div>
                          <div v-for="orgReq in orgRequest_pending" v-bind:key="orgReq.id">
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >Organisation</label>
                                <div class="col-sm-3"> 
                                    <input type="text" disabled class="form-control" name="organisation" v-model="orgReq.name" placeholder="">
                                </div>
                                <label for="" class="col-sm-1 control-label" >ABN/ACN</label>
                                <div class="col-sm-3"> 
                                    <input type="text" disabled class="form-control" name="organisation" v-model="orgReq.abn" placeholder="">
                                </div>
                                <label><i class="fa fa-hourglass-o fa-2x" ></i> Pending Approval</label>
                              </div>
                          </div>
                          <div v-for="orgReq in orgRequest_amendment_requested" v-bind:key="orgReq.id">
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >Organisation</label>
                                <div class="col-sm-3">
                                    <input type="text" disabled class="form-control" name="organisation" v-model="orgReq.name" placeholder="">
                                </div>
                                <label for="" class="col-sm-1 control-label" >ABN/ACN</label>
                                <div class="col-sm-3">
                                    <input type="text" disabled class="form-control" name="organisation" v-model="orgReq.abn" placeholder="">
                                </div>
                                    <span class="btn btn-info btn-file float-start">
                                        Upload New File <input type="file" ref="uploadedFile" @change="uploadNewFileUpdateOrgRequest(orgReq)"/>
                                    </span>
                                    <span class="float-start" style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                              </div>
                          </div>

                          <div v-if="managesOrg=='Consultant' && addingCompany">
                              <h3>New Organisation (as consultant)</h3>
                              <div class="form-group">
                                  <label for="" class="col-sm-2 control-label" >Organisation</label>
                                  <div class="col-sm-6">
                                      <input type="text" class="form-control" name="organisation" v-model="newOrg.name" placeholder="">
                                  </div>
                              </div>
                              <div class="form-group">
                                  <label for="" class="col-sm-2 control-label" >ABN/ACN</label>
                                  <div class="col-sm-6">
                                      <input type="text" class="form-control" name="abn" v-model="newOrg.abn" placeholder="">
                                  </div>
                                  <div class="col-sm-2">
                                      <button v-if="newOrg.detailsChecked" @click.prevent="checkOrganisation()" class="btn btn-primary">Check Details</button>
                                  </div>
                              </div>
                              <div class="form-group">
                                    <label class="col-sm-12" style="text-align:left;">
                                      Please upload a letter with an organisation letterhead stating that you are a consultant for the organisation.
                                        <span class="btn btn-info btn-file">
                                            Attach File <input type="file" ref="uploadedFile" @change="readFile()"/>
                                        </span>
                                        <span  style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                                    </label>
                                    <br/>

                                    <label for="" class="col-sm-10 control-label" style="text-align:left;">You will be notified by email once the Department has checked the organisation details.
                                    </label>


                                    <div class="col-sm-12">
                                      <button v-if="!registeringOrg" @click.prevent="orgConsultRequest()" class="btn btn-primary float-start">Submit</button>
                                      <button v-else disabled class="btn btn-primary float-end"><i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting</button>
                                    </div>
                              </div>
                           </div>




                          <div style="margin-top:15px;" v-if="managesOrg=='Yes' && addingCompany">
                              <h3>New Organisation</h3>
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >Organisation</label>
                                <div class="col-sm-6">
                                    <input type="text" class="form-control" name="organisation" v-model="newOrg.name" placeholder="">
                                </div>
                              </div>
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >ABN/ACN</label>
                                <div class="col-sm-6">
                                    <input type="text" class="form-control" name="abn" v-model="newOrg.abn" placeholder="">
                                </div>
                                <div class="col-sm-2">
                                    <button @click.prevent="checkOrganisation()" class="btn btn-primary">Check Details</button>
                                </div>
                              </div>
                              <div class="form-group" v-if="newOrg.exists && newOrg.detailsChecked">
                                  <label class="col-sm-12" style="text-align:left;margin-bottom:20px;">
                                    This organisation has already been registered with the system. Please enter the two pin codes below.<br/>
                                    These pin codes can be retrieved from one of the following people:<br/> {{newOrg.first_five}}
                                  </label>
                                  <label for="" class="col-sm-2 control-label" >Pin 1</label>
                                  <div class="col-sm-2">
                                    <input type="text" class="form-control" name="abn" v-model="newOrg.pin1" placeholder="">
                                  </div>
                                  <label for="" class="col-sm-2 control-label" >Pin 2</label>
                                  <div class="col-sm-2">
                                    <input type="text" class="form-control" name="abn" v-model="newOrg.pin2" placeholder="">
                                  </div>
                                  <div class="col-sm-2">
                                    <button v-if="!validatingPins" @click.prevent="validatePins()" class="btn btn-primary float-start">Validate</button>
                                    <button v-else class="btn btn-primary float-start"><i class="fa fa-spin fa-spinner"></i>&nbsp;Validating Pins</button>
                                  </div>
                              </div>
                              <div class="form-group" v-else-if="!newOrg.exists && newOrg.detailsChecked">
                                  <label class="col-sm-12" style="text-align:left;">
                                    This organisation has not yet been registered with this system. Please upload a letter with an organisation letterhead stating that you are an employee of this organisation.<br/>
                                  </label>
                                  <div class="col-sm-12">
                                    <span class="btn btn-info btn-file float-start">
                                        Attach File <input type="file" ref="uploadedFile" @change="readFile()"/>
                                    </span>
                                    <span class="float-start" style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                                  </div>
                                  <label for="" class="col-sm-10 control-label" style="text-align:left;">You will be notified by email once the Department has checked the organisation details.</label>
                                  <div class="col-sm-12">
                                    <button v-if="!registeringOrg" @click.prevent="orgRequest()" class="btn btn-primary float-end">Submit</button>
                                    <button v-else disabled class="btn btn-primary float-end"><i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting</button>
                                  </div>
                              </div>
                              <div class="form-group" v-else-if="newOrg.exists && !newOrg.detailsChecked">
                                  <label class="col-sm-12" style="text-align:left;">
                                    Please upload a letter with an organisation letterhead stating that you are an employee of this organisation.<br/>
                                  </label>
                                  <div class="col-sm-12">
                                    <span class="btn btn-info btn-file float-start">
                                        Attach File <input type="file" ref="uploadedFile" @change="readFile()"/>
                                    </span>
                                    <span class="float-start" style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                                  </div>
                                  <label for="" class="col-sm-10 control-label" style="text-align:left;">You will be notified by email once the Department has checked the organisation details.</label>
                                  <div class="col-sm-12">
                                    <button v-if="!registeringOrg" @click.prevent="orgRequest()" class="btn btn-primary float-end">Submit</button>
                                    <button v-else disabled class="btn btn-primary float-end"><i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting</button>
                                  </div>
                              </div>
                              
                        </div>
                       </form>
                  </div>
                </FormSection>
            </div>
        </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import $ from 'jquery'
import { api_endpoints, helpers, fetch_util } from '@/utils/hooks'
// import SecureBaseLink from '@/components/common/securebase_link.vue';
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'MyUserDetails',
    components: {
        FormSection,
        // SecureBaseLink,
    },
    data () {
        return {
            oBody: 'oBody'+uuid(),
            current_user: {
                wildlifecompliance_organisations:[],
            },
            newOrg: {
                'name': '',
                'abn': '',
                'detailsChecked': false,
                'exists': false
            },
            loading: [],
            registeringOrg: false,
            validatingPins: false,
            addingCompany: false,
            managesOrg: 'No',
            managesOrgConsultant: 'No',
            uploadedFile: null,
            uploadedID: null,

            updatingPersonal: false,
            updatingAddress: false,
            updatingContact: false,
            role:null,
            orgRequest_pending:[],
            orgRequest_amendment_requested:[],
            new_user: false,
            datepickerOptions:{
                format: 'YYYY-MM-DD',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            showCompleteMsg:false,
        }
    },
    watch: {
        managesOrg: function() {
            if (this.managesOrg == 'Yes'){
              this.newOrg.detailsChecked = false;
              this.role = 'employee'
            } else if (this.managesOrg == 'Consultant'){
              this.newOrg.detailsChecked = false;
              this.role ='consultant'
            }else{this.role = null
              this.newOrg.detailsChecked = false;
            }

            if (this.managesOrg  == 'Yes' && !this.hasOrgs && this.newOrg){
                this.addCompany()

            } else if (this.managesOrg == 'No' && this.newOrg){
                this.resetNewOrg();
                this.uploadedFile = null;
                this.addingCompany = false;
            } else if (this.managesOrg == 'Consultant' && this.newOrg) {
                this.addCompany();
            } else {
                this.addCompany()
                this.addingCompany=false
            }
        },
  
    },
    computed: {
        hasOrgs: function() {
            if (this.current_user) {
                return this.current_user.wildlifecompliance_organisations && this.current_user.wildlifecompliance_organisations.length > 0 ? true: false;
            }
            return false;
        },
        uploadedFileName: function() {
            return this.uploadedFile != null ? this.uploadedFile.name: '';
        },
    },
    methods: {
        readFile: function() {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.uploadedFile)[0];
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(input.files[0]); 
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            vm.uploadedFile = _file;
        },
        readFileID: async function() {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.uploadedID)[0];
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(input.files[0]);
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            vm.uploadedID = _file;
            await vm.uploadID();
        },
        addCompany: function (){
            this.newOrg.push = {
                'name': '',
                'abn': '',
            };
            this.addingCompany=true;
        },
        resetNewOrg: function(){
            this.newOrg = {
                'detailsChecked': false,
                'exists': false
            };
        },
        checkOrganisation: function() {
            console.log('Entered CheckOrg')
            let vm = this;
            let new_organisation = vm.newOrg;
            for (var organisation in vm.current_user.wildlifecompliance_organisations) {
                if (new_organisation.abn && vm.current_user.wildlifecompliance_organisations[organisation].abn == new_organisation.abn) {
                    swal.fire({
                        title: 'Checking Organisation',
                        text: 'You are already associated with this organisation.',
                        icon: 'info',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    return;
                }
            }
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,'existence'), {method:'POST', body:JSON.stringify(this.newOrg)},{
                emulateJSON:true
            })
            request.then((response) => {
                this.newOrg.exists = response.exists;
                this.newOrg.id = response.id;
                this.newOrg.detailsChecked = false;
                if (response.first_five) {
                  this.newOrg.first_five = response.first_five;
                  this.newOrg.detailsChecked = true;
                }
                this.newOrg.detailsChecked = this.newOrg.exists ? this.newOrg.detailsChecked : true;
            }, (error) => {
                this.newOrg.detailsChecked = false;
                let error_msg = '<br/>';
                for (var key in error.body) {
                    if (key==='non_field_errors'){
                        error_msg += error.body[key] + '<br/>';
                    } else {
                        error_msg += key + ': ' + error.body[key] + '<br/>';
                    }
                }
                swal.fire({
                    title: 'Checking Organisation',
                    text: 'There was an error checking this organisation.<br/>' + error_msg,
                    icon: 'error',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                    },
                })
            });
        },
        validatePins: function() {
            let vm = this;
            vm.validatingPins = true;
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,(vm.newOrg.id+'/validate_pins')), {method:'POST', body:JSON.stringify(this.newOrg)},{
                emulateJSON:true
            })
            request.then((response) => {
                if (response.valid){
                    swal.fire({
                        title:'Validate Pins',
                        text:'The pins you entered have been validated and your request will be processed by Organisation Administrator.',
                        icon:'success',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();

                    let request = fetch_util.fetchUrl(api_endpoints.my_user_details)
                    request.then((response) => {
                        vm.current_user = response
                        if ( vm.current_user.wildlifecompliance_organisations && vm.current_user.wildlifecompliance_organisations.length > 0 ) { vm.managesOrg = 'Yes' }
                    }).catch((error) => {
                        console.log(error);
                    });

                }else {
                    swal.fire({
                        title:'Validate Pins',
                        text:'The pins you entered were incorrect', 
                        icon:'error',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                }
                vm.validatingPins = false;
            }, (error) => {
                console.log(error);
                vm.validatingPins = false;
            });
        },
        orgRequest: function() {
            let vm = this;
            vm.registeringOrg = true;
            let data = new FormData();
            data.append('name', vm.newOrg.name);
            data.append('abn', vm.newOrg.abn);
            data.append('identification', vm.uploadedFile);
            data.append('role',vm.role);
            vm.newOrg.name = vm.newOrg.name == null ? '' : vm.newOrg.name
            vm.newOrg.abn = vm.newOrg.abn == null ? '' : vm.newOrg.abn
            if (vm.newOrg.name == '' || vm.newOrg.abn == '' || vm.uploadedFile == null){
                vm.registeringOrg = false;
                swal.fire({
                    title:'Error submitting organisation request',
                    text:'Please enter the organisation details and attach a file before submitting your request.',
                    icon:'error',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                    },
                })
            } else {
                console.log(data)
                let request = fetch_util.fetchUrl(api_endpoints.organisation_requests,{method:'POST', body:data},{})
                request.then(() => {
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    swal.fire({
                        title: 'Sent',
                        html: 'Your organisation request has been successfully submitted.',
                        icon: 'success',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    }).then(() => {
                        if (this.$route.name == 'account'){
                           window.location.reload(true);
                        }
                    });
                }, (error) => {
                    vm.registeringOrg = false;
                    let error_msg = '<br/>';
                    for (var key in error.body) {
                        if (key==='non_field_errors'){
                            error_msg += error.body[key] + '<br/>';
                        } else {
                            error_msg += key + ': ' + error.body[key] + '<br/>';
                        }
                    }
                    swal.fire({
                        title:'Error submitting organisation request',
                        text:error_msg,
                        icon:'error',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    });
                });
            }
        },
        orgConsultRequest: function() {
            let vm = this;
            vm.registeringOrg = true;
            let data = new FormData();
            let new_organisation = vm.newOrg;
            for (var organisation in vm.current_user.wildlifecompliance_organisations) {
                if (new_organisation.abn && vm.current_user.wildlifecompliance_organisations[organisation].abn == new_organisation.abn) {
                    swal.fire({
                        title: 'Checking Organisation',
                        text: 'You are already associated with this organisation.',
                        icon: 'info',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    return;
                }
            }
            data.append('name', vm.newOrg.name);
            data.append('abn', vm.newOrg.abn);
            data.append('identification', vm.uploadedFile);
            data.append('role',vm.role);
            vm.newOrg.name = vm.newOrg.name == null ? '' : vm.newOrg.name
            vm.newOrg.abn = vm.newOrg.abn == null ? '' : vm.newOrg.abn
            if (vm.newOrg.name == '' || vm.newOrg.abn == '' || vm.uploadedFile == null){
                vm.registeringOrg = false;
                swal.fire({
                    title:'Error submitting organisation request',
                    text:'Please enter the organisation details and attach a file before submitting your request.',
                    icon:'error',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                    },
                })
            } else {
                console.log(data)
                let request = fetch_util.fetchUrl(api_endpoints.organisation_requests,{method:'POST', body:data},{})
                request.then(() => {
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    swal.fire({
                        title: 'Sent',
                        text: 'Your organisation request has been successfully submitted.',
                        icon: 'success',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    }).then(() => {
                        if (this.$route.name == 'account'){
                           window.location.reload(true);
                        }
                    });
                }, (error) => {
                    vm.registeringOrg = false;
                    let error_msg = '<br/>';
                    for (var key in error.body) {
                        if (key==='non_field_errors'){
                            error_msg += error.body[key] + '<br/>';
                        } else {
                            error_msg += key + ': ' + error.body[key] + '<br/>';
                        }
                    }
                    swal.fire({
                        title:'Error submitting organisation request',
                        text:error_msg,
                        icon:'error',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    });
                });
            }
        },
        uploadNewFileUpdateOrgRequest: function(orgReq) {
            let vm = this;
            vm.readFile();
            let data = new FormData();
            data.append('identification', vm.uploadedFile);
            let request = fetch_util.fetchUrl(
                helpers.add_endpoint_json(api_endpoints.organisation_requests,orgReq.id+'/reupload_identification_amendment_request')
            ,{method:"PUT",body:JSON.stringify(data)},
            {
                emulateJSON:true
            })
            request.then(() => {
                vm.uploadedFile = null;
                vm.resetNewOrg();
                swal.fire({
                    title: 'Sent',
                    text: 'Your organisation request has been successfully submitted.',
                    icon: 'success',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                    },
                }).then(() => {
                    window.location.reload(true);
                });
            }, (error) => {
                console.log(error);
                vm.registeringOrg = false;
                let error_msg = '<br/>';
                for (var key in error.body) {
                    error_msg += key + ': ' + error.body[key] + '<br/>';
                }
                swal.fire({
                    title:'Error submitting organisation request',
                    text:error_msg,
                    icon:'error',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                    },
                });
            });
        },
        toggleSection: function (e) {
            let el = e.target;
            let chev = null;
            $(el).on('click', function () {
                chev = $(this);
                $(chev).toggleClass('glyphicon-chevron-down glyphicon-chevron-up');
            })
        },
        fetchOrgRequestPending:function (){
            let vm =this;
            fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,'get_pending_requests')).then((response)=>{
                vm.orgRequest_pending = response;
                vm.loading.splice('fetching pending organisation requests',1);
            }).catch((error) => {
                console.log(error)
            });
        },
        fetchOrgRequestAmendmentRequested:function (){
            let vm =this;
            fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,'get_amendment_requested_requests')).then((response)=>{
                vm.orgRequest_amendment_requested = response;
                vm.loading.splice('fetching amendment requested organisation requests',1);
            }).catch((error) => {
                console.log(error)
            });
        },
        unlinkUser: function(org){
            let vm = this;
            let org_name = org.name;
        
            swal.fire({
                title: "Unlink From Organisation",
                text: "Are you sure you want to be unlinked from "+org.name+" ?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then((result) => {
                if (result.isConfirmed) {
                    let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,org.id+'/unlink_user'), {method:'POST', body:JSON.stringify(vm.current_user)},{
                        emulateJSON:true
                    })
                    request.then(() => {
                        let request = fetch_util.fetchUrl(api_endpoints.my_user_details)
                        request.then((response) => {
                            vm.current_user = response
                            if ( vm.current_user.wildlifecompliance_organisations && vm.current_user.wildlifecompliance_organisations.length > 0 ) { vm.managesOrg = 'Yes' }
                        }).catch((error) => {
                            console.log(error);
                        });
                        swal.fire({
                            title:'Unlink',
                            text:'You have been successfully unlinked from '+org_name+'.',
                            icon:'success',
                            customClass: {
                                confirmButton: 'btn btn-primary',
                            },
                        })
                    }, (error) => {
                        let error_msg = '<br/>';
                        for (var key in error.body) {
                            if (key == 'non_field_errors') { error_msg += error.body[key] + '<br/>'; }
                        }
                        swal.fire({
                            title:'Unlink',
                            text:'There was an error unlinking you from '+org_name+'.' + error_msg,
                            icon:'error',
                            customClass: {
                                confirmButton: 'btn btn-primary',
                            },
                        })
                    });
                }
            },(error) => {
                console.log(error);
            }); 
        },
    },
    beforeRouteEnter: function(to,from,next){
        let request = fetch_util.fetchUrl(api_endpoints.my_user_details)
        request.then((response) => {
            if (to.name == 'first-time' && response.address_details && response.personal_details && response.contact_details && response.has_complete_first_time){
                window.location.href='/';
            }
            else{
                next(vm => {
                    vm.current_user = response
                    if (vm.current_user.wildlifecompliance_organisations && vm.current_user.wildlifecompliance_organisations.length > 0) { vm.managesOrg = 'Yes' }
                });
            }
        }).catch((error) => {
            console.log(error);
        });
    },
    mounted: function(){
        this.fetchOrgRequestPending();
        this.fetchOrgRequestAmendmentRequested();
        this.personal_form = document.forms.personal_form;
        $('.panelClicker[data-toggle="collapse"]').on('click', function () {
            var chev = $(this).children()[0];
            window.setTimeout(function () {
                $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
            },100);
        });
        let request = fetch_util.fetchUrl(api_endpoints.is_new_user)
        request.then((response) => {
            this.new_user = response;
        }).catch((error) => {
            console.log(error);
        });
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.btn-file {
    position: relative;
    overflow: hidden;
}
.btn-file input[type=file] {
    position: absolute;
    top: 0;
    right: 0;
    min-width: 100%;
    min-height: 100%;
    font-size: 100px;
    text-align: right;
    filter: alpha(opacity=0);
    opacity: 0;
    outline: none;
    background: white;
    cursor: inherit;
    display: block;
}
</style>