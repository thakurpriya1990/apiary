<template id="comms_logs">
    <div class="">
        <div class="card mb-3">
            <div class="card-header">Logs</div>
            <div class="card-body border-bottom">
                <label for="assigned-to" class="form-label"
                    >Communication Logs</label
                >
                <div class="rounded border py-2">
                    <span class="ps-3 pe-2"
                        ><i class="bi bi-card-list"></i>
                    </span>
                    <a ref="showCommsBtn" href="#" class="pe-5" @click.prevent="showComms()"
                        >Show</a
                    >
                    <template v-if="!disable_add_entry">
                        <span class="pe-2">
                            <i class="bi bi-plus-circle"></i>
                        </span>
                        <a ref="addCommsBtn" href="#" @click.prevent="addComm()"
                            >Add Entry</a
                        >
                    </template>
                </div>
            </div>
            <div class="card-body">
                <label for="assigned-to" class="form-label">Action Logs</label>
                <div class="rounded border py-2">
                    <span class="ps-3 pe-2"
                        ><i class="bi bi-card-list"></i>
                    </span>
                    <a ref="showActionBtn" href="#" @click.prevent>Show</a>
                </div>
            </div>
        </div>
        <AddCommLog ref="add_comm" :url="comms_add_url" />
        <ShowCommsLogs ref="show_comms" :url="comms_url" />
    </div>
</template>

<script>
import AddCommLog from './add_comm_log.vue';
import ShowCommsLogs from './show_comms_logs.vue';
import { constants, helpers } from '@/utils/hooks';
import { v4 as uuid } from 'uuid';
import $ from 'jquery';

export default {
    name: 'CommsLogSection',
    components: {
        AddCommLog,
        ShowCommsLogs,
    },
    props: {
        comms_url: {
            type: String,
            required: true,
        },
        logs_url: {
            type: String,
            required: true,
        },
        comms_add_url: {
            type: String,
            required: true,
        },
        disable_add_entry: {
            type: Boolean,
            default: true,
        },
    },
    data() {
        let vm = this;
        return {
            uuid: uuid(),
            dateFormat: 'DD/MM/YYYY HH:mm:ss',
            actionsTable: null,
            popoversInitialised: false,
            actionsDtOptions: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                deferRender: true,
                autowidth: true,
                order: [[3, 'desc']], // order the non-formatted date as a hidden column
                dom:
                    "<'row'<'col-sm-4'l><'col-sm-8'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'row'<'col-sm-5'i><'col-sm-7'p>>",
                processing: true,
                ajax: {
                    url: vm.logs_url,
                    dataSrc: '',
                },
                columns: [
                    {
                        title: 'Who',
                        data: 'who',
                        orderable: false,
                    },
                    {
                        title: 'What',
                        data: 'what',
                        orderable: false,
                    },
                    {
                        title: 'When',
                        data: 'when',
                        orderable: false,
                        mRender: function (data) {
                            return moment(data).format(vm.dateFormat);
                        },
                    },
                    {
                        title: 'Created',
                        data: 'when',
                        visible: false,
                    },
                ],
            },
        };
    },
    mounted: function () {
        let vm = this;
        this.$nextTick(() => {
            vm.initialisePopovers();
        });
    },
    methods: {
        initialiseActionLogs: function () {
            // To allow table elements (ref: https://getbootstrap.com/docs/5.1/getting-started/javascript/#sanitizer)
            var myDefaultAllowList = bootstrap.Tooltip.Default.allowList;
            myDefaultAllowList.table = [];
            let vm = this;
            let actionLogId = 'actions-log-table' + vm.uuid;
            let popover_name = 'popover-' + vm.uuid + '-logs';
            let popover_elem = $(vm.$refs.showActionBtn)[0];
            let my_content =
                '<table id="' +
                actionLogId +
                '" class="hover table border table-striped table-bordered dt-responsive" cellspacing="0" width="100%"></table>';
            let my_template =
                '<div class="popover ' +
                popover_name +
                '" role="tooltip"><div class="popover-arrow" style="top:110px;"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>';
            new bootstrap.Popover(popover_elem, {
                html: true,
                content: my_content,
                template: my_template,
                title: 'Action logs',
                container: 'body',
                placement: 'auto',
                trigger: 'click',
            });
            popover_elem.addEventListener('inserted.bs.popover', () => {
                // when the popover template has been added to the DOM
                vm.actionsTable = $('#' + actionLogId).DataTable(
                    this.actionsDtOptions
                );
                vm.actionsTable.on('draw', () => {
                    const selector = `#${actionLogId} [data-bs-toggle="popover"]`;
                    document.querySelectorAll(selector).forEach((el) => {
                        if (el._bsPopover) return;
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
            });
            popover_elem.addEventListener('shown.bs.popover', () => {
                // when the popover has been made visible to the user
                let el = vm.$refs.showActionBtn;
                var popover_bounding_top = parseInt(
                    $('.' + popover_name)[0].getBoundingClientRect().top
                );
                var el_bounding_top = parseInt(
                    $(el)[0].getBoundingClientRect().top
                );
                var diff = el_bounding_top - popover_bounding_top;
                var x = diff + 5;
                $('.' + popover_name)
                    .children('.arrow')
                    .css('top', x + 'px');
            });
        },
        initialisePopovers: function () {
            if (!this.popoversInitialised) {
                this.initialiseActionLogs();
                this.popoversInitialised = true;
            }
        },
        addComm() {
            this.$refs.add_comm.isModalOpen = true;
        },
        showComms() {
            this.$refs.show_comms.isModalOpen = true;
        },
    },
};
</script>
