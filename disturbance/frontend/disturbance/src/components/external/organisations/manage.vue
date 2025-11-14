<template>
    <div class="container" v-if="org && loaded" id="userInfo">
        <div class="row" >
            <div class="col-sm-12">
                <FormSection
                    :form-collapse="false"
                    label="Contact Details"
                    index="contact_details"
                    subtitle="View and update the organisation's contact details"
                >
                    <div class="card-body" >
                        <div class="row">
                            <div class="col-md-12">
                            <button @click.prevent="addContact()" style="margin-bottom:10px;" class="btn btn-primary float-end">Add Contact</button>
                            </div>
                        </div>
                        <div class="row">
                            <form class="form-horizontal" action="index.html" method="post">
                                <datatable ref="contacts_datatable" id="organisation_contacts_datatable" :dtOptions="contacts_options" :dtHeaders="contacts_headers"/>
                            </form>
                        </div>
                  </div>
                </FormSection>
            </div>
        </div>
        <div v-if="myorgperms.is_admin && org && loaded" class="row">
            <div class="col-sm-12">
                <FormSection
                    :form-collapse="false"
                    label="Linked Persons"
                    index="linked_persons"
                    subtitle="Manage the user accounts linked to the organisation"
                >
                    <div class="panel panel-default">
                        <div class="col-sm-12 row form-group">
                            <h6>Use the Organisation Administrator pin codes if you want the new user to be linked as organisation administrator.<br> Use the Organisation User pin codes if you want the new user to be linked as organisation user.</h6>
                        </div>
                        <form class="form-horizontal" action="index.html" method="post">
                             <div class="row form-group">
                                    <div class="col-sm-6">
                                        <label for="" class="control-label"> Organisation User Pin Code 1:</label>
                                    </div>
                                    <div class="col-sm-6">
                                        {{org.pins.three}}
                                    </div>
                                    <div class="col-sm-6">
                                        <label for="" class="control-label" >Organisation User Pin Code 2:</label>
                                    </div>
                                    <div class="col-sm-6">
                                        {{org.pins.four}}
                                    </div>
                            </div>
                            
                             <div class="row form-group" :disabled ='!myorgperms.is_admin'>
                                    <div class="col-sm-6">
                                        <label for="" class="control-label"> Organisation Administrator Pin Code 1:</label>
                                    </div>
                                    <div class="col-sm-6">
                                        {{org.pins.one}}
                                    </div>
                                    <div class="col-sm-6">
                                        <label for="" class="control-label" >Organisation Administrator Pin Code 2:</label>
                                    </div>
                                    <div class="col-sm-6">
                                       {{org.pins.two}}
                                    </div>
                            </div>
                        </form>
                        <div class="col-sm-12 row">
                            <div class="col-sm-12 row">
                                <div class="row">
                                    <div class="col-sm-12 top-buffer-s">
                                        <strong>Persons linked to the organisation are controlled by the organisation. The Department cannot manage this list of people.</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-sm-12 row">
                            <datatable ref="contacts_datatable_user" id="organisation_contacts_datatable_ref" :dtOptions="contacts_options_ref" :dtHeaders="contacts_headers_ref"/>
                        </div>
                    </div>
                </FormSection>
            </div>
        </div>
        <AddContact v-if="loaded" v-model="isAddContactModalOpen" :org_id="org_id" />
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import { api_endpoints, helpers, fetch_util , constants} from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import utils from '../utils.js'
import api from '../api.js'
import AddContact from '@common-utils/add_contact.vue'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'ManageOrganisation',
    data () {
        let vm = this;
        return {
            isAddContactModalOpen: false,
            cBody: 'cBody'+uuid(),
            oBody: 'oBody'+uuid(),
            org_id: null,
            org: null,
            myorgperms: null,
            loaded: false,
            contact_user: {
                first_name: null,
                last_name: null,
                email: null,
                mobile_number: null,
                phone_number: null,
                user_role: {}
            },
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            contacts_headers:["Name","Phone","Mobile","Fax","Email","Action"],
            contacts_options:{
                 language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    "url": '',
                    "dataSrc": ''
                },
                columns: [
                    {
                        data:'last_name',
                        mRender:function (data,type,full) {
                            return full.first_name + " " + full.last_name;
                        }
                    },
                    {data:'phone_number'},
                    {data:'mobile_number'},
                    {data:'fax_number'},
                    {data:'email'},
                    {
                        data:'user_status',
                        mRender:function (data,type,full) {
                            let links = '';
                            let name = full.first_name + ' ' + full.last_name;
                            if (full.user_status.id == 'draft' ){
                                links +=  `<a data-email='${full.email}' data-name='${name}' data-id='${full.id}' class="remove-contact">Remove</a><br/>`;
                                
                            }
                            return links;
                        }
                    }
                  ],
                  processing: true
                
            },

            contacts_headers_ref:["Name","Role","Email","Status","Action"],
            contacts_options_ref:{
               language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    "url": '',
                    "dataSrc": ''
                },
                columns: [
                    {
                        data:'last_name',
                        mRender:function (data,type,full) {
                            return full.first_name + " " + full.last_name;
                        }
                    },
                    {
                        data:'user_role',
                        mRender:function (data,type,full) {
                            return full.user_role;
                        }
                    },
                    {data:'email'},
                    {
                        data:'user_status',
                        mRender:function (data,type,full) {
                            return full.user_status;
                        }
                    },
                    {
                        data:'id',
                        mRender:function (data,type,full) {
                            let links = '';
                            if (vm.myorgperms.is_admin){
                                if(full.user_status.id == 'pending'){
                                    links +=  `<a data-email='${full.email}' data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="accept_contact">Accept</a><br/>`;
                                    links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="decline_contact">Decline</a><br/>`;
                                } else if(full.user_status.id == 'suspended'){
                                    links +=  `<a data-email='${full.email}' data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="reinstate_contact">Reinstate</a><br/>`;
                                } else if(full.user_status.id == 'active'){
                                    links +=  `<a data-email='${full.email}' data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="unlink_contact">Unlink</a><br/>`;
                                    links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="suspend_contact">Suspend</a><br/>`;
                                    if(full.user_role.id == 'organisation_user'){
                                        links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="make_admin_contact">Make Organisation Admin</a><br/>`;
                                        links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="make_consultant">Make Organisation Consultant</a><br/>`;
                                    } else if (full.user_role.id == 'organisation_admin') {
                                        links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="make_user_contact">Make Organisation User</a><br/>`;
                                        links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="make_consultant">Make Organisation Consultant</a><br/>`;
                                    } else {
                                        links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="make_admin_contact">Make Organisation Admin</a><br/>`;
                                        links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="make_user_contact">Make Organisation User</a><br/>`;
                                    }
                                } else if(full.user_status.id == 'unlinked'){
                                    links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="relink_contact">Reinstate</a><br/>`;
                                } else if(full.user_status.id == 'declined'){
                                    links +=  `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="accept_declined_contact">Accept (Previously Declined)</a><br/>`;
                                }
                            }        
                            return links;
                        }
                    }
                ],
                processing: true,
                                  
            }
        }
    },
    components: {
        datatable,
        AddContact,
        FormSection
    },
    beforeRouteEnter: function(to, from, next){
        let id = [utils.fetchOrganisationId(to.params.org_id)];
        Promise.all(id).then(res => {
            let initialisers = [
                utils.fetchOrganisation(res[0].id),
                utils.fetchOrganisationPermissions(res[0].id)
            ]
            Promise.all(initialisers).then(data => {
                next(vm => {
                    vm.org_id = res[0].id;
                    vm.org = data[0];
                    vm.myorgperms = data[1];
                    vm.org.address = vm.org.address != null ? vm.org.address : {};
                    vm.org.pins = vm.org.pins != null ? vm.org.pins : {};
                });
            });
        });
    },
    beforeRouteUpdate: function(to, from, next){
        let id = [utils.fetchOrganisationId(to.params.org_id)];
        Promise.all(id).then(res => {
            let initialisers = [
                utils.fetchOrganisation(res[0].id),
                utils.fetchOrganisationPermissions(res[0].id)
            ]
            Promise.all(initialisers).then(data => {
                next(vm => {
                    vm.org_id = res[0].id;
                    vm.org = data[0];
                    vm.myorgperms = data[1];
                    vm.org.address = vm.org.address != null ? vm.org.address : {};
                    vm.org.pins = vm.org.pins != null ? vm.org.pins : {};
                });
            });
        });
    },
    methods: {
        addContact: function() {
            this.isAddContactModalOpen = true;
        },
        eventListeners: function(){
            let vm = this;
            vm.$refs.contacts_datatable.vmDataTable.on('click','.remove-contact',(e) => {
                e.preventDefault();

                let name = $(e.target).data('name');
                let email = $(e.target).data('email');
                let id = $(e.target).data('id');
                swal.fire({
                    title: "Delete Contact",
                    text: "Are you sure you want to remove "+ name + " (" + email + ") as a contact?",
                    icon: "error",
                    showCancelButton: true,
                    confirmButtonText: 'Accept'
                }).then((result) => {
                    if (result){
                        vm.deleteContact(id);
                    }
                },(error) => {
                    console.log(error);
                });
            });

            vm.$refs.contacts_datatable_user.vmDataTable.on('click','.accept_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname 
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email 
                vm.contact_user.mobile_number= mobile 
                vm.contact_user.phone_number= phone 


                swal.fire({
                    title: "Contact Accept",
                    text: "Are you sure you want to accept contact request " + name + " (" + email + ")?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed){
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/accept_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Contact Accept',
                                text: 'You have successfully accepted ' + name + '.',
                                icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            }).then(() => {
                                vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                            },(error) => {
                                console.log('Swal error: '+error);
                            });
                        }).catch((error) => {
                            swal.fire({
                                title:'Contact Accept',
                                text:'There was an error accepting ' + name + '.',
                                icon:'error',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            console.log(error?.message || JSON.stringify(error));
                        });
                    }
                },(error) => {
                    console.log(error);
                });
            });


            vm.$refs.contacts_datatable_user.vmDataTable.on('click','.accept_declined_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email
                vm.contact_user.mobile_number= mobile
                vm.contact_user.phone_number= phone


                swal.fire({
                    title: "Contact Accept (Previously Declined)",
                    text: "Are you sure you want to accept the previously declined contact request for " + name + " (" + email + ")?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed){
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/accept_declined_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Contact Accept (Previously Declined)',
                                text: 'You have successfully accepted ' + name + '.',
                                icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                           }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log(error);
                            });
                         }).catch((error) => {
                            swal.fire({
                                title:'Contact Accept (Previously Declined)',
                                text:'There was an error accepting ' + name + '.',
                                icon:'error',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            console.log(error?.message || JSON.stringify(error));
                        });
                    }
                },(error) => {
                    console.log(error);
                });
            });



            vm.$refs.contacts_datatable_user.vmDataTable.on('click','.decline_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname 
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email 
                vm.contact_user.mobile_number= mobile 
                vm.contact_user.phone_number= phone 
                // console.log(vm.contact_user)


                swal.fire({
                    title: "Contact Decline",
                    text: "Are you sure you want to decline the contact request for " + name + " (" + email + ")?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    }
                }).then((result) => {
                    if (result){
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/decline_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Contact Decline',
                                text: 'You have successfully declined ' + name + '.',
                                icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            }).catch((error) => {
                                swal.fire({
                                    title:'Contact Decline',
                                    text:'There was an error declining ' + name + '.',
                                    icon:'error',
                                    customClass: {
                                        confirmButton: 'btn btn-primary',
                                    },
                                });
                                console.log(error?.message || JSON.stringify(error));
                            });
                        }, (error) => {
                            swal.fire({
                                title:'Contact Decline',
                                text:'There was an error declining ' + name + '.',
                                icon:'error',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            console.log(error?.message || JSON.stringify(error));
                        });
                    }
                },(error) => {
                    console.log(error);
                });
            });




            vm.$refs.contacts_datatable_user.vmDataTable.on('click','.unlink_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname 
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email 
                vm.contact_user.mobile_number= mobile 
                vm.contact_user.phone_number= phone 


                swal.fire({
                    title: "Unlink",
                    text: "Are you sure you want to unlink " + name + " (" + email + ")?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed){
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/unlink_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Unlink',
                                text: 'You have successfully unlinked ' + name + '.',
                                icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                           }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log(error);
                            });
                        }, (error) => {
                            let error_msg = '<br/>';
                            for (var key in error.body) {
                              if (key == 'non_field_errors') { error_msg += error.body[key] + '<br/>'; }
                            }
                            swal.fire({
                              title:'Unlink User',
                              text:'There was an error unlinking ' + name + ' from the Organisation.' + error_msg,
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
            });


            vm.$refs.contacts_datatable_user.vmDataTable.on('click','.make_admin_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname 
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email 
                vm.contact_user.mobile_number= mobile 
                vm.contact_user.phone_number= phone 


                swal.fire({
                    title: "Organisation Admin",
                    text: "Are you sure you want to make " + name + " (" + email + ") an Organisation Admin?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed) {
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/make_admin_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Organisation Admin',
                                text: 'You have successfully made ' + name + ' an Organisation Admin.',
                                icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log('Swal error:'+error);
                            });
                        }).catch((error) => {
                            swal.fire({
                                title:'Organisation Admin',
                                text:'There was an error making ' + name + ' an Organisation Admin.',
                                icon:'error',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            console.log(error?.message || JSON.stringify(error));
                        });
                    }
                },(error) => {
                    console.log(error);
                });
            });


            vm.$refs.contacts_datatable_user.vmDataTable.on('click','.make_user_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname 
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email 
                vm.contact_user.mobile_number= mobile 
                vm.contact_user.phone_number= phone 


                swal.fire({
                    title: "Organisation User",
                    text: "Are you sure you want to make " + name + " (" + email + ") an Organisation User?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed) {
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/make_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Organisation User',
                                text: 'You have successfully made ' + name + ' an Organisation User.',
                               icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log('Swal error:'+error);
                            });
                        }, (error) => {
                            let error_msg = '<br/>';
                            for (var key in error.body) {
                              if (key == 'non_field_errors') { error_msg += error.body[key] + '<br/>'; }
                            }
                            swal.fire({
                              title:'Organisation User',
                              text:'There was an error making ' + name + ' an Organisation User.' + error_msg,
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
            });




            vm.$refs.contacts_datatable_user.vmDataTable.on('click','.suspend_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname 
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email 
                vm.contact_user.mobile_number= mobile 
                vm.contact_user.phone_number= phone 


                swal.fire({
                    title: "Suspend User",
                    text: "Are you sure you want to Suspend  " + name + " (" + email + ")?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed) {
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/suspend_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Suspend User',
                                text: 'You have successfully suspended ' + name + ' as a User.',
                                icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log('Swal error:'+error);
                            });
                        }, (error) => {
                            let error_msg = '<br/>';
                            for (var key in error.body) {
                              if (key == 'non_field_errors') { error_msg += error.body[key] + '<br/>'; }
                            }
                            swal.fire({
                              title:'Suspend User',
                              text:'There was an error suspending ' + name + ' as a User.' + error_msg,
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
            });



             vm.$refs.contacts_datatable_user.vmDataTable.on('click','.reinstate_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname 
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email 
                vm.contact_user.mobile_number= mobile 
                vm.contact_user.phone_number= phone 


                swal.fire({
                    title: "Reinstate User",
                    text: "Are you sure you want to Reinstate  " + name + " (" + email + ")?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed) {
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/reinstate_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Reinstate User',
                                text: 'You have successfully reinstated ' + name + '.',
                                icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log('Swal error:'+error);
                            });
                        }).catch((error) => {
                            swal.fire('Reinstate User','There was an error reinstating ' + name + '.','error',{
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            console.log(error?.message || JSON.stringify(error));
                        });
                    }
                },(error) => {
                    console.log(error);
                });
            });


             vm.$refs.contacts_datatable_user.vmDataTable.on('click','.relink_contact',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');

                vm.contact_user.first_name= firstname
                vm.contact_user.last_name= lastname
                vm.contact_user.email= email
                vm.contact_user.mobile_number= mobile
                vm.contact_user.phone_number= phone


                swal.fire({
                    title: "Relink User",
                    text: "Are you sure you want to Relink  " + name + " (" + email + ")?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                     customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed) {
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/relink_user'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Relink User',
                                text: 'You have successfully relinked ' + name + '.',
                               icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log('Swal error:'+error);
                            });
                         }).catch((error) => {
                            swal.fire('Relink User','There was an error relink ' + name + '.','error',{
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            });
                            console.log(error?.message || JSON.stringify(error));
                        });
                    }
                },(error) => {
                    console.log(error);
                });
            });

            vm.$refs.contacts_datatable_user.vmDataTable.on('click','.make_consultant',(e) => {
                e.preventDefault();

                let firstname = $(e.target).data('firstname');
                let lastname = $(e.target).data('lastname');
                let name = firstname + ' ' + lastname;
                let email = $(e.target).data('email');
                // let id = $(e.target).data('id');
                let mobile = $(e.target).data('mobile');
                let phone = $(e.target).data('phone');
                let role = 'consultant';

                vm.contact_user.first_name= firstname;
                vm.contact_user.last_name= lastname;
                vm.contact_user.email= email;
                vm.contact_user.mobile_number= mobile;
                vm.contact_user.phone_number= phone;
                vm.contact_user.user_role.id = role;

                swal.fire({
                    title: "Organisation Consultant",
                    text: "Are you sure you want to make " + name + " (" + email + ") an Organisation Consultant?",
                    showCancelButton: true,
                    confirmButtonText: 'Accept',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                        cancelButton: 'btn btn-secondary',
                    },
                }).then((result) => {
                    if (result.isConfirmed) {
                        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org.id+'/make_consultant'), {method:'POST', body:JSON.stringify(vm.contact_user)},{
                            emulateJSON:true
                        })
                        request.then(() => {
                            swal.fire({
                                title: 'Organisation Consultant',
                                text: 'You have successfully made ' + name + ' an Organisation Consultant.',
                                icon: 'success',
                                confirmButtonText: 'Okay',
                                customClass: {
                                    confirmButton: 'btn btn-primary',
                                },
                            }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log('Swal error:'+error);
                            });
                        }, (error) => {
                            let error_msg = '<br/>';
                            for (var key in error.body) {
                              if (key == 'non_field_errors') { error_msg += error.body[key] + '<br/>'; }
                            }
                            swal.fire({
                              title:'Organisation Consultant',
                              text:'There was an error making ' + name + ' an Organisation Consultant.' + error_msg,
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
            });


        },
        addedContact: function() {
            let vm = this;
            swal.fire({
                title:'Added',
                text:'The contact has been successfully added.',
                icon:'success',
                customClass: {
                    confirmButton: 'btn btn-primary',
                },
            })
            vm.$refs.contacts_datatable.vmDataTable.ajax.reload();
        },
        deleteContact: function(id){
            let vm = this;
            
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.organisation_contacts,id), {method:"DELETE"},{
                emulateJSON:true
            })
            request.then(() => {
                swal.fire({
                    title:'Contact Deleted', 
                    text:'The contact was successfully deleted.',
                    icon:'success',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                    },
                })
                vm.$refs.contacts_datatable.vmDataTable.ajax.reload();
             }).catch((error) => {
                console.log(error);
                swal.fire({
                    title:'Contact Deleted', 
                    text:'The contact could not be deleted because of the following error: ' + error,
                    icon:'error',
                    customClass: {
                        confirmButton: 'btn btn-primary',
                    },
                })
            });
        },
        unlinkUser: function(d){
            let vm = this;
            let org = vm.org;
            let org_name = org.name;
            let person = helpers.copyObject(d);
            swal.fire({
                title: "Unlink From Organisation",
                text: "Are you sure you want to unlink " + person.name + " from " + org.name + "?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then((result) => {
                if (result.isConfirmed) {
                    let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,org.id+'/unlink_user'),{method:'POST', body:JSON.stringify({'user':person.id})},{
                        emulateJSON:true
                    })
                    request.then((response) => {
                        vm.org = response;
                        if (vm.org.address == null){ vm.org.address = {}; }
                        swal.fire({
                            title: 'Unlink',
                            text: 'You have successfully unlinked ' + person.name + ' from ' + org_name + '.',
                            type: 'success',
                            confirmButtonText: 'Okay',
                            customClass: {
                                confirmButton: 'btn btn-primary',
                            },
                       }).then((result) => {
                                if(result.isConfirmed){
                                    vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                }
                            },(error) => {
                                console.log('Swal error:'+error);
                            });
                    }, (error) => {
                        let error_msg = '<br/>';
                        for (var key in error.body) {
                          if (key == 'non_field_errors') { error_msg += error.body[key] + '<br/>'; }
                        }
                        swal.fire({
                          title:'Unlink User',
                          text:'There was an error unlinking ' + person.name + ' from the Organisation.' + error_msg,
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
        }
    },
    mounted: function(){
        this.personal_form = document.forms.personal_form;
        //this.loaded = true;
    },
    updated: function(){
        $('.panelClicker[data-toggle="collapse"]').on('click', function () {
            var chev = $(this).children()[0];
            window.setTimeout(function () {
                $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
            },100);
        }); 
        this.$nextTick(() => {
            this.eventListeners();
        });
    },
    watch: {
        org_id: function() {
            let vm = this;
            if (vm.org_id != null) {
                console.log(vm.contacts_options_ref.ajax)
                vm.contacts_options.ajax.url = helpers.add_endpoint_json(api_endpoints.organisations,vm.org_id+'/contacts');
                vm.contacts_options_ref.ajax.url= helpers.add_endpoint_json(api_endpoints.organisations,vm.org_id+'/contacts_exclude');
                vm.loaded = true;
            }
        }
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.top-buffer-s {
    margin-top: 25px;
}
</style>