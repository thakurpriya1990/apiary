<template lang="html">
    <div>

        <template v-if="is_internal">
            <div class="form-group row">
                <label class="col-sm-3">Do not charge annual site fee until</label>
                <div class="col-sm-3">
                    <div class="input-group date" ref="untilDatePicker">
                        <input type="text" class="form-control text-center" placeholder="DD/MM/YYYY" id="no_charge_until" :readonly="is_readonly"/>
                        <span class="input-group-addon">
                            <span class="glyphicon glyphicon-calendar"></span>
                        </span>
                    </div>
                </div>
                <div class="col-sm-6 text-right">
                    <template v-if="saving_date">
                        <button class="btn btn-primary" type="button" disabled>
                              <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                              Saving...
                        </button>
                    </template>
                    <template v-else>
                        <button type="button" class="btn btn-primary" @click="noChargeUntilButtonClicked">Save</button>
                    </template>
                </div>
            </div>
        </template>

        <div class="form-group row">
            <label class="col-sm-3">Calendar year</label>
            <div class="col-sm-4">
                <select class="form-control" v-model="year_name_selected">
                    <template v-if="annual_rental_fee_periods">
                        <option value="all">
                            All
                        </option>
                    </template>
                    <template v-for="annual_rental_fee_period in annual_rental_fee_periods" :key="annual_rental_fee_period.id">
                        <option :value="annual_rental_fee_period.year_name">
                            {{ annual_rental_fee_period.year_name }}
                        </option>
                    </template>
                </select>
            </div>
        </div>

        <div class="form-group row">
            <label class="col-sm-3">Invoice</label>
            <div class="col-sm-9">
                <template v-for="annual_rental_fee_period in annual_rental_fee_periods">
                    <template v-if="annual_rental_fee_period.year_name == year_name_selected || year_name_selected == 'all'">
                        <template v-for="annual_rental_fee in annual_rental_fee_period.annual_rental_fees" :key="annual_rental_fee.id">
                            <div>
                                <a :href="'/payments/invoice-pdf/' + annual_rental_fee.invoice_reference + '.pdf'" target='_blank'>
                                    <i style='color:red;' class='fa fa-file-pdf-o'></i> #{{ annual_rental_fee.invoice_reference }}
                                </a>
                                <strong>Payment status: {{ capitalize(annual_rental_fee.payment_status) }}</strong>
                                <template v-if="annual_rental_fee.payment_status === 'unpaid'">
                                    <a :href="'/annual_rental_fee/' + annual_rental_fee.id">Pay</a>
                                </template>
                            </div>
                        </template>
                    </template>
                </template>
            </div>
        </div>

    </div>
</template>

<script>
    export default {
        name: 'SectionAnnualRentalFee',
        props:{
            email: {
                type: String,
                default: '',
            },
            is_readonly: {
                type: Boolean,
                default: true,
            },
            is_internal: {
                type: Boolean,
                default: false,
            },
            is_external: {
                type: Boolean,
                default: false,
            },
            no_annual_rental_fee_until: {
                type: String,  // Expect YYYY-MM-DD format
                default: '',
            },
            annual_rental_fee_periods: {
                type: Array,
                default: function(){
                    return []
                }
            },
            approval_id: {
                type: Number,
                default: null,
            }
        },
        watch: {
            occupier_email: function(){
                this.emitContentsChangedEvent();
            },
        },
        data: function(){
            return {
                occupier_email: this.email,  // Copy props to the local variable
                year_name_selected: null,
                until_date: null,
                saving_date: false,
            }
        },
        created: function(){
            // Copy the values from props (it is not allowd to change props' value)
            if (this.no_annual_rental_fee_until){
                if (this.no_annual_rental_fee_until instanceof moment) {
                    this.until_date = this.no_annual_rental_fee_until.format('DD/MM/YYYY');
                } else {
                    // Wrong type of object, clear it
                    console.warn('The value passed to from_date is wrong type');
                    this.until_date = null;
                }
            }

        },
        mounted: function(){
            let vm = this;
            this.$nextTick(() => {
                vm.addEventListeners();
            });
        },
        components: {

        },
        computed: {

        },
        methods: {
            capitalize: function(s){
                if (typeof s !== 'string') return ''
                s = s.replace(/_/g, " ")
                return s.charAt(0).toUpperCase() + s.slice(1)
            },
            noChargeUntilButtonClicked: function() {
                this.saving_date = true
                let vm = this
                console.log(vm.until_date)
                fetch('/api/approvals/' + vm.approval_id + '/no_charge_until_date/',
                    {
                        headers: { 'Content-Type': 'application/json' },
                        method: 'POST',
                        body: JSON.stringify({
                            'until_date': vm.until_date,
                        }),
                    }).then(
                    async (response)=>{
                        if (!response.ok) {
                            const errorBody = await response.json();
                            throw errorBody;
                        }
                        swal.fire({
                            title:'Saved',
                            text:'Date has been saved',
                            icon:'success',
                            customClass: {
                                confirmButton: 'btn btn-primary',
                            },
                        });
                        this.saving_date = false
                    }).catch(error => {
                        console.log(error);
                        this.saving_date = false
                    });
            },
            addEventListeners: function () {
                console.log('in addEventListener')
                let vm = this;
                let el_until = $(vm.$refs.untilDatePicker);
                let options = {
                    format: "DD/MM/YYYY",
                    showClear: true ,
                    useCurrent: false,
                };

                el_until.datetimepicker(options);

                el_until.on("dp.change", function(e) {
                    let selected_date = null;
                    if (e.date){
                        // Date selected
                        selected_date = e.date.format('DD/MM/YYYY')  // e.date is moment object
                        vm.until_date = selected_date;
                    } else {
                        // Date not selected
                        vm.until_date = selected_date;
                    }
                });


                //***
                // Set dates in case they are passed from the parent component
                //***
                let searchPattern = /^[0-9]{4}/

                let until_date = vm.no_annual_rental_fee_until
                if (until_date) {
                    console.log('until_date')
                    console.log(until_date)
                    // If date passed
                    if (searchPattern.test(until_date)) {
                        // Convert YYYY-MM-DD to DD/MM/YYYY
                        until_date = moment(until_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
                    }
                    $('#no_charge_until').val(until_date);
                }
            },
            emitContentsChangedEvent: function () {
                this.$emit('contents_changed', {
                    'occupier_email': this.occupier_email,
                });
            },
        },
    }
</script>

<style lang="css" scoped>
</style>
