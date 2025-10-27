// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import resource from 'vue-resource'
import App from './App'
import router from './router'
import 'bootstrap'
import helpers from '@/utils/helpers'
// import hooks from './packages'
import api_endpoints from './api'

import $ from 'jquery';
import { extendMoment } from 'moment-range';
import jsZip from 'jszip';
window.JSZip = jsZip;
window.$ = $;

import 'datatables.net';
import 'datatables.net-bs';
import 'datatables.net-responsive-bs';
import 'datatables.net-buttons/js/dataTables.buttons.js'
import 'datatables.net-buttons/js/buttons.html5.js'

import "datatables.net-bs/css/dataTables.bootstrap.css"
import "datatables.net-responsive-bs/css/responsive.bootstrap.css"

import "sweetalert2/dist/sweetalert2.css"

import 'jquery-validation'


extendMoment(moment);

require( '../node_modules/bootstrap/dist/css/bootstrap.css' );
//require('../node_modules/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css')
require( '../node_modules/font-awesome/css/font-awesome.min.css' )
require('../node_modules/eonasdan-bootstrap-datetimepicker')
require('../node_modules/jquery.easing')

Vue.config.devtools = true;
Vue.config.productionTip = false
Vue.use( resource );
Vue.prototype.$log = console.log

// Add CSRF Token to every request
Vue.http.interceptors.push( function ( request, next ) {
  // modify headers
  if ( request.url != api_endpoints.countries ) {
    request.headers.set( 'X-CSRFToken', helpers.getCookie( 'csrftoken' ) );
  }

  // continue to next interceptor
  next();
} );


/* eslint-disable no-new */
new Vue( {
  el: '#app',
  router,
  template: '<App/>',
  components: {
    App
  }
} )
