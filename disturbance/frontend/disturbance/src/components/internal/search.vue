<template>
  <div class="container" id="internalSearch">
    <div class="row">
      <div class="col-sm-12">
        <FormSection
          :form-collapse="false"
          label="Search Organisations"
          Index="search-organisation"
        >
          <div class="row">
            <form name="searchOrganisationForm">
              <div class="mb-3">
                <div class="row">
                  <div class="col-md-8">
                    <div class="input-group">
                      <div class="flex-grow-1">
                        <select
                          ref="searchOrg"
                          class="form-select"
                          name="organisation"
                        ></select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </FormSection>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-12">
        <FormSection
          :form-collapse="false"
          label="Search Keywords"
          Index="search-keywords"
        >
          <div class="row">
            <div class="col-lg-12">
              <div class="mb-3">
                <label for="" class="col-form-label col-lg-12 fs-5"
                  >Filter</label
                >
                <div class="form-check col-md-3">
                  <input
                    class="form-check-input"
                    ref="searchProposal"
                    id="searchProposal"
                    name="searchProposal"
                    type="checkbox"
                    v-model="searchProposal"
                  />
                  <label class="form-check-label fw-normal" for="searchProposal"
                    >Proposal</label
                  >
                </div>
                <div class="form-check col-md-3">
                  <input
                    class="form-check-input"
                    ref="searchApproval"
                    id="searchApproval"
                    name="searchApproval"
                    type="checkbox"
                    v-model="searchApproval"
                  />
                  <label class="form-check-label fw-normal" for="searchApproval"
                    >Approval</label
                  >
                </div>
                <div class="form-check form-check-inline col-md-3">
                  <input
                    class="form-check-input"
                    ref="searchCompliance"
                    id="searchCompliance"
                    name="searchCompliance"
                    type="checkbox"
                    v-model="searchCompliance"
                  />
                  <label
                    class="form-check-label fw-normal"
                    for="searchCompliance"
                    >Compliance with requirements</label
                  >
                </div>
                <label for="" class="col-form-label col-lg-12 fs-5"
                  >Keyword(s)</label
                >
                <div class="row">
                  <div class="col-md-4">
                    <div class="input-group">
                      <input
                        ref="keyWord"
                        type="search"
                        class="form-control"
                        name="details"
                        placeholder=""
                        v-model="keyWord"
                      />
                      <button
                        type="button"
                        @click.prevent="add"
                        class="btn btn-primary"
                      >
                        <i class="bi bi-plus-lg me-2"></i>Add Keyword
                      </button>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <div>
                      <button
                        v-if="searching"
                        type="button"
                        class="btn btn-primary btn-margin me-3"
                        value="Search"
                        disabled
                      >
                        <i class="bi bi-search me-2"></i>Search<i
                          class="fa fa-circle-o-notch fa-spin fa-fw"
                        ></i>
                      </button>
                      <button
                        v-else
                        type="button"
                        @click.prevent="search"
                        class="btn btn-primary btn-margin me-3"
                        value="Search"
                      >
                        <i class="bi bi-search me-2"></i>Search
                      </button>
                      <button
                        type="reset"
                        @click.prevent="reset"
                        class="btn btn-primary"
                        value="Clear"
                      >
                        <i class="bi bi-x me-2"></i>Clear All Keywords
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="row mb-3">
            <div class="col-lg-12">
              <ul class="list-inline">
                <li
                  class="list-inline-item"
                  v-for="(item, i) in searchKeywords"
                  :key="i"
                >
                  <button @click.prevent="" class="btn btn-light border">
                    {{ item
                    }}<a href="" @click.prevent="removeKeyword(i)"
                      ><span class="bi bi-x ps-2"></span
                    ></a>
                  </button>
                </li>
              </ul>
            </div>
          </div>

          <div class="row mb-2"></div>

          <div class="row">
            <div class="col-lg-12">
              <datatable
                ref="proposal_datatable"
                class="border rounded p-2"
                :id="datatable_id"
                :dtOptions="proposal_options"
                :dtHeaders="proposal_headers"
              />
            </div>
          </div>
        </FormSection>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-12">
        <FormSection
          :form-collapse="false"
          label="Search Reference Number"
          Index="search-reference"
        >
          <div class="row mb-1">
            <div class="row">
              <div class="col-md-4">
                <div class="input-group">
                  <input
                    ref="referenceWord"
                    type="search"
                    class="form-control input-sm"
                    name="referenceWord"
                    placeholder="reference number"
                    v-model="referenceWord"
                    required
                    @input="resetError"
                  />
                  <input
                    type="button"
                    @click.prevent="search_reference($refs.referenceWord)"
                    class="btn btn-primary"
                    value="Search"
                  />
                </div>
              </div>
            </div>
            <div class="mt-3">
              <alert v-if="showError" type="danger"
                ><strong>{{ errorString }}</strong></alert
              >
            </div>
          </div>
        </FormSection>
      </div>
    </div>
  </div>
</template>
<script>
import { v4 as uuid } from "uuid";
import datatable from "@/utils/vue/datatable.vue";
import FormSection from "@/components/forms/section_toggle.vue";
import alert from "@vue-utils/alert.vue";
import { api_endpoints, constants } from "@/utils/hooks";
import utils from "@/components/internal/utils";

import $ from "jquery";
export default {
  name: "SearchComponent",
  props: {},
  data() {
    let vm = this;
    return {
      rBody: "rBody" + uuid(),
      oBody: "oBody" + uuid(),
      kBody: "kBody" + uuid(),
      loading: [],
      filtered_url: api_endpoints.filtered_users + "?search=",
      searchKeywords: [],
      searchProposal: true,
      searchApproval: false,
      searchCompliance: false,
      referenceWord: "",
      keyWord: null,
      selected_organisation: "",
      organisations: null,
      searching: false,
      results: [],
      errors: false,
      errorString: "",
      datatable_id: "proposal-datatable-" + uuid(),
      proposal_headers: ["Number", "Type", "Proponent", "Text found", "Action"],
      proposal_options: {
        language: {
          processing: constants.DATATABLE_PROCESSING_HTML,
        },
        responsive: true,
        data: vm.results,
        columns: [
          { data: "number", defaultContent: "" },
          { data: "type", defaultContent: "" },
          { data: "applicant", defaultContent: "" },
          {
            //data: "text.value"
            data: "text",
            mRender: function (data) {
              if (data.value) {
                return data.value;
              } else {
                return data;
              }
            },
            defaultContent: "",
          },
          {
            data: "id",
            mRender: function (data, type, full) {
              let links = "";
              if (full.type == "Proposal") {
                links += `<a href='/internal/proposal/${full.id}'>View</a><br/>`;
              }
              if (full.type == "Compliance") {
                links += `<a href='/internal/compliance/${full.id}'>View</a><br/>`;
              }
              if (full.type == "Approval") {
                links += `<a href='/internal/approval/${full.id}'>View</a><br/>`;
              }
              return links;
            },
            defaultContent: "",
          },
        ],
        processing: true,
      },
    };
  },
  components: {
    datatable,
    alert,
    FormSection,
  },
  computed: {
    showError: function () {
      var vm = this;
      return vm.errors;
    },
  },
  methods: {
    resetError: function () {
      let vm = this;
      vm.errors = false;
      vm.errorString = "";
    },
    addListeners: function () {
      let vm = this;
      // Initialise select2 for region
      $(vm.$refs.searchOrg)
        .select2({
          theme: "bootstrap-5",
          width: "100%",
          allowClear: true,
          placeholder: "Start Typing to Search for an Organisation",
        })
        .on("select2:select", function (e) {
          var selected = $(e.currentTarget);
          vm.selected_organisation = selected.val();
        })
        .on("select2:unselect", function (e) {
          var selected = $(e.currentTarget);
          vm.selected_organisation = selected.val();
        });
    },

    viewUserDetails: function () {
      let vm = this;
      let form = document.forms.searchUserForm;
      var user_selected = form.elements["User-selected"];
      if (user_selected != undefined || user_selected != null) {
        var user_id = user_selected.value;
        vm.$router.push({
          name: "internal-user-detail",
          params: { user_id: user_id },
        });
      } else {
        swal
          .fire({
            title: "User not selected",
            html: "Please select the user to view the details",
            icon: "error",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          })
          .then(() => {});
        return;
      }
    },

    add: function () {
      let vm = this;
      if (
        vm.keyWord != null &&
        vm.keyWord.trim() != "" &&
        !vm.searchKeywords.includes(vm.keyWord)
      ) {
        vm.searchKeywords.push(vm.keyWord);
        vm.keyWord = null;
        this.$refs.keyWord.focus();
      }
    },
    removeKeyword: function (index) {
      let vm = this;
      if (index > -1) {
        vm.searchKeywords.splice(index, 1);
      }
      this.$refs.keyWord.focus();
    },
    reset: function () {
      let vm = this;
      if (vm.searchKeywords != null) {
        vm.searchKeywords = [];
      }
      vm.keyWord = null;
      vm.results = [];
      this.$refs.keyWord.focus();
      vm.$refs.proposal_datatable.vmDataTable.clear();
      vm.$refs.proposal_datatable.vmDataTable.draw();
    },

    search: function () {
      let vm = this;
      if (this.searchKeywords.length > 0) {
        vm.searching = true;
        fetch("/api/search_keywords.json", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            searchKeywords: vm.searchKeywords,
            searchProposal: vm.searchProposal,
            searchApproval: vm.searchApproval,
            searchCompliance: vm.searchCompliance,
            is_internal: true,
          }),
        })
          .then(async (res) => {
            if (!res.ok) {
              throw new Error(`HTTP error! Status: ${res.status}`);
            }
            vm.results = await res.json();
            vm.$refs.proposal_datatable.vmDataTable.clear();
            vm.$refs.proposal_datatable.vmDataTable.rows.add(vm.results);
            vm.$refs.proposal_datatable.vmDataTable.draw();
            vm.searching = false;
          })
          .catch((err) => {
            console.log(err);
            vm.searching = false;
          });
      }
    },

    search_reference: async function (inputEl) {
      let vm = this;

      vm.errors = false;
      vm.errorString = "";

      if (!vm.referenceWord) {
        inputEl?.focus();
        return;
      }

      if (vm.referenceWord) {
        try {
          const res = await fetch("/api/search_reference.json", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              reference_number: vm.referenceWord,
            }),
          });

          const data = await res.json();

          if (!res.ok) {
            throw new Error(data);
          }

          vm.errors = false;
          vm.errorString = "";
          vm.$router.push({
            path: "/internal/" + data.type + "/" + data.id,
          });
        } catch (error) {
          console.log(error);
          vm.errors = true;
          vm.errorString = error;
        }
      }
    },
  },
  mounted: function () {
    let vm = this;
    vm.proposal_options.data = vm.results;
    vm.$refs.proposal_datatable.vmDataTable.draw();
    $('a[data-bs-toggle="collapse"]').on("click", function () {
      var chev = $(this).children()[0];
      window.setTimeout(function () {
        $(chev).toggleClass("fa-chevron-down fa-chevron-up");
      }, 100);
    });
    this.$nextTick(() => {
      vm.addListeners();
    });
  },
};
</script>
