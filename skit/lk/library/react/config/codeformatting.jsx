/**
 * @license
 * Copyright 2016 Cluster Labs, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var codeformatting = React.createClass({
  getInitialState: function() {
    return {
      lang: this.props.lang
    };
  },

  formatSample: function(props) {
    var dataType;
    var funcName;
    var value;

    if (props.setting.kind == 'bool') {
      dataType = 'BOOL ';
      funcName = 'LKConfigBool';
      if (props.lang == 'obj-c') {
        value = (props.setting.value == 'false') ? 'NO' : 'YES';
      } else {
        value = props.setting.value;
      }
    }
    if (props.setting.kind == 'string') {
      dataType = 'NSString *';
      funcName = 'LKConfigString';
      value = '"'+props.setting.value+'"'
    }
    if (props.setting.kind == 'int') {
      dataType = 'NSInteger ';
      funcName = 'LKConfigInteger';
      value = props.setting.value;
    }
    if (props.setting.kind == 'float') {
      dataType = 'double ';
      funcName = 'LKConfigDouble';
      value = props.setting.value;
    }

    this.setState({
      lang: props.lang,
      dataType: dataType,
      funcName: funcName,
      value: value
    })
  },

  componentWillMount: function() {
    this.formatSample(this.props);
  },

  componentWillReceiveProps: function(nextProps) {
    this.formatSample(nextProps);
  },

  render: function() {
    switch (this.props.lang) {
      case 'obj-c':
        return (
          <span>
            {this.state.dataType}{this.props.setting.key} = {this.state.funcName}(@"{this.props.setting.key}", {this.state.value});
          </span>
        )
        break;

      case 'swift':
        return (
          <span>
            let {this.props.setting.key} = {this.state.funcName}("{this.props.setting.key}", {this.state.value})
          </span>
        )
        break;

      default:
        return (
          <span>{this.state.funcName}(<span className="string">"{this.props.setting.key}"</span>);</span>
        )
        break;
    }
  }

});

module.exports = codeformatting;