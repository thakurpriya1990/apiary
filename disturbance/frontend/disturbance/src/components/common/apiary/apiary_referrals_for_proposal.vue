<template id="apiary-referrals-for-proposal">
    <div>
        <a v-if="!isFinalised" href="#" ref="showRef"  @click.prevent class="actionBtn top-buffer-s">Show Referrals</a>
    </div> 

</template>

<script>
import { v4 as uuid } from 'uuid';
import {
    api_endpoints,
    helpers,
    constants
}from '@/utils/hooks'

export default {
    name: 'ApiaryReferrals',
    props: {
        isFinalised: {
            type: Boolean,
            required: true
        },
        canAction: {
            type: Boolean,
            required: true
        },
        proposal: {
            type: Object,
            required: true
        },
        referral_url: {
            type: String,
            default: null
        }
    },
    data(){
        let vm = this;
        return {
            dateFormat: 'DD/MM/YYYY HH:mm:ss',
            datatable_url: '',
            datatable_options: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                popoversInitialised: false,
                responsive: true,
                deferRender: true, 
                autowidth: true,
                //order: [[0, 'desc']],
                processing:true,
                ajax: { 
                    "url": this.referral_url,
                    "dataSrc": '',
                },
                columns:[
                    {
                        title: 'Sent On',
                        data: 'lodged_on',
                        render: function (date) {
                            return moment(date).format(vm.dateFormat);
                        }
                    },
                    {
                        title: 'Referral Group',
                        data: 'id',
                        render: function (data,type,full){
                            let referralGroup = '';
                            if (full.apiary_referral && full.apiary_referral.referral_group && full.apiary_referral.referral_group.name) {
                                referralGroup = full.apiary_referral.referral_group.name;
                            }
                            return referralGroup; 
                        }
                    },
                    {
                        title: 'Status',
                        data: 'referral_status'
                    },
                    {
                        title: 'Action',
                        data: 'id',
                        render: function (data,type,full) {
                            var result = '';
                            if (!vm.canAction){
                                return result;
                            }
                            var user = full.apiary_referral.referral_group.name; 
                            //var user = 'dummy val';
                            let apiaryId = full.apiary_referral.id
                            if (full.referral_status == 'Awaiting'){
                                result = `<a href="#" data-id="${apiaryId}" data-user="${user}" class="remindRef">Remind</a>/<a href="#" data-id="${apiaryId}" data-user="${user}" class="recallRef">Recall</a>`;
                            }
                            else{
                                result = `<a href="#" data-id="${apiaryId}" data-user="${user}" class="resendRef">Resend</a>`;
                            }
                            return result;
                        }
                    },
                    {
                        title: 'Referral Comments',
                        data: 'referral_text',

                        'render': function (value) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 20,
                                    omission: ellipsis,
                                    separator: ' '
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template('<a href="#" ' +
                                    'role="button" ' +
                                    'data-toggle="popover" ' +
                                    'data-trigger="click" ' +
                                    'data-placement="top auto"' +
                                    'data-html="true" ' +
                                    'data-content="<%= text %>" ' +
                                    '>more</a>');
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: value
                                });
                            }

                            return result;
                        },
                        'createdCell': helpers.dtPopoverCellFn,
                    }
                ]
            },
            refTable: null,
        }
    },
    methods: {
        remindReferral:function(_id,user){
            let vm = this;
            
            fetch(helpers.add_endpoint_json(api_endpoints.apiary_referrals,_id+'/remind')).then(
                async (response) => {
                    if (!response.ok) {
                        return response.json().then(err => { throw err });
                    }
                    let referrals_remind_res = await response.json();
                    vm.$emit('refreshFromResponse',referrals_remind_res);
                    vm.refTable.ajax.reload();
                    swal.fire({
                        title: 'Referral Reminder',
                        text: 'A reminder has been sent to '+user,
                        icon: 'success',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                }).catch(error => {
                    swal.fire({
                        title: 'Proposal Error',
                        text: error,
                        icon: 'error',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                }
            );
        },
        resendReferral:function(_id,user){
            let vm = this;
            fetch(helpers.add_endpoint_json(api_endpoints.apiary_referrals,_id+'/resend')).then(
                async (response) => {
                    if (!response.ok) {
                        return response.json().then(err => { throw err });
                    }
                    let referrals_resend_res = await response.json();
                    vm.$emit('refreshFromResponse',referrals_resend_res);
                    vm.refTable.ajax.reload();
                    swal.fire({
                        title: 'Referral Resent',
                        text: 'The referral has been resent to '+user,
                        icon: 'success',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                }).catch(error => {
                    swal.fire({
                        title: 'Proposal Error',
                        text: error,
                        icon: 'error',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                }
            );
        },
        recallReferral:function(_id,user){
            let vm = this;
            
            fetch(helpers.add_endpoint_json(api_endpoints.apiary_referrals,_id+'/recall')).then(
                async (response) => {
                    if (!response.ok) {
                        return response.json().then(err => { throw err });
                    }
                    let ref_recall_res = await response.json()
                    vm.$emit('refreshFromResponse',ref_recall_res);
                    vm.refTable.ajax.reload();
                    swal.fire({
                        title: 'Referral Recall',
                        text: 'The referral has been recalled from '+user,
                        icon: 'success',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                }).catch(error => {
                    swal.fire({
                        title: 'Proposal Error',
                        text: error,
                        icon: 'error',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    })
                }
            );
        },
        initialiseTable: function(){
            var myDefaultAllowList = bootstrap.Tooltip.Default.allowList;
            myDefaultAllowList.table = [];
            let vm = this;
            let referralId = 'referral-table' + vm.uuid;
            let popover_name = 'popover-' + vm.uuid + '-referrals';
            let popover_elem = $(vm.$refs.showRef)[0];
            let my_content =
                '<table id="' +
                referralId +
                '" class="hover table border table-striped table-bordered dt-responsive" cellspacing="0"></table>';
            let my_template =
                '<div class="popover ' +
                popover_name +
                '" role="tooltip"><div class="popover-arrow" style="top:110px;"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>';
            new bootstrap.Popover(popover_elem, {
                sanitize: false,
                html: true,
                content: my_content,
                template: my_template,
                title: 'Referrals',
                container: 'body',
                placement: 'auto',
                trigger: 'click',
            });
            popover_elem.addEventListener('inserted.bs.popover', () => {
                // when the popover template has been added to the DOM
                vm.refTable = $('#' + referralId).DataTable(
                    vm.datatable_options
                );
                vm.refTable.on('draw', () => {
                    const selector = `#${referralId} [data-bs-toggle="popover"]`;
                    document.querySelectorAll(selector).forEach((el) => {
                        if (el._bsPopover) return; // already initialised
                        new bootstrap.Popover(el, {
                            container: 'body',
                            trigger:
                                el.getAttribute('data-bs-trigger') || 'click',
                            html:
                                (
                                    el.getAttribute('data-bs-html') || ''
                                ).toLowerCase() === 'true',
                        });
                    });
                });
                
                $('#' + referralId).on('click.ref', 'a.resendRef', function (e) {
                    e.preventDefault();
                    vm.resendReferral($(this).data('id'), $(this).data('user'));
                });

                $('#' + referralId).on('click.ref', 'a.recallRef', function (e) {
                    e.preventDefault();
                    vm.recallReferral($(this).data('id'), $(this).data('user'));
                });

                $('#' + referralId).on('click.ref', 'a.remindRef', function (e) {
                    e.preventDefault();
                    vm.remindReferral($(this).data('id'), $(this).data('user'));
                });

            });

            popover_elem.addEventListener('shown.bs.popover', () => {
                var el = vm.$refs.showRef;
                var popover_bounding_top = parseInt($('.'+popover_name)[0].getBoundingClientRect().top);
                var el_bounding_top = parseInt($(el)[0].getBoundingClientRect().top);
                var diff = el_bounding_top - popover_bounding_top;
                var x = diff + 5;
                $('.'+popover_name).children('.arrow').css('top', x + 'px');
            })
        },
        initialisePopovers: function () {
            if (!this.popoversInitialised) {
                this.initialiseTable();
                this.popoversInitialised = true;
            }
        },
    },
    mounted(){
        let vm = this;
        this.$nextTick(() => {
            vm.initialisePopovers();
        }); 
    }
}
</script>

<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
</style>
