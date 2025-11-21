<template>
    <div class="container">
        <template v-if="is_local">
            site_transitions.vue
        </template>
        <FormSection :formCollapse="false" label="Site(s)" Index="site_avaiability">
            <ComponentSiteSelection
                :apiary_sites="apiary_sites"
                :is_internal="true"
                :is_external="false"
                :show_col_checkbox="false"
                :show_col_status="true"
                :show_col_previous_site_holder="true"
                :show_action_make_vacant="true"
                :key="component_site_selection_key"
                @apiary_sites_updated="apiarySitesUpdated"
            />
        </FormSection>
    </div>
</template>

<script>
    import FormSection from "@/components/forms/section_toggle.vue"
    import ComponentSiteSelection from '@/components/common/apiary/component_site_selection.vue'
    import { v4 as uuid } from 'uuid';
    import { helpers, } from "@/utils/hooks.js"

    export default {
        name: 'SiteTransitions',
        data: function(){
            return {
                component_site_selection_key: uuid(),
                apiary_sites: [],
                is_local: helpers.is_local(),
            }
        },
        components: {
            ComponentSiteSelection,
            FormSection,
        },
        props: {

        },
        computed: {

        },
        methods: {
            apiarySitesUpdated: function(apiary_sites){
                console.log(apiary_sites)
            },
            loadSites: async function() {
                let vm = this

                fetch('/api/apiary_site/transitable_sites/')
                .then(async (res) => {
                    if (!res.ok) { return res.json().then(err => { throw err }); }
                    const data = await res.json();
                    vm.apiary_sites = data.features
                    this.component_site_selection_key = uuid()

                    ////let temp_use = data.apiary_temporary_use
                    //vm.apiary_temporary_use = data.apiary_temporary_use
                    //if (vm.apiary_temporary_use.from_date){
                    //    console.log(vm.apiary_temporary_use.from_date);
                    //    vm.apiary_temporary_use.from_date = moment(vm.apiary_temporary_use.from_date, 'YYYY-MM-DD');
                    //    console.log(vm.apiary_temporary_use.from_date);
                    //}
                    //if (vm.apiary_temporary_use.to_date){
                    //    console.log(vm.apiary_temporary_use.to_date);
                    //    vm.apiary_temporary_use.to_date = moment(vm.apiary_temporary_use.to_date, 'YYYY-MM-DD');
                    //    console.log(vm.apiary_temporary_use.to_date);
                    //}

                    //// Update PeriodAndSites component
                    //vm.period_and_sites_key = uuid();
                    //// Update TemporaryOccupier component
                    //vm.temporary_occupier_key = uuid();
                }).catch(err => {
                    console.log(err);
                });
            },
        },
        created: function() {
            this.loadSites()
        },
        mounted: function() {

        },
    }
</script>

<style>

</style>
