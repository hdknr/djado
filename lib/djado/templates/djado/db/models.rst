{% load i18n djadotags %}

{% header_label app.verbose_name 0 %} 

.. contents::
    :local:

{% for opt in app|app_model_opts %}

.. _{{ opt.app_label }}.models.{{ opt.object_name }}:

{% header_label opt.verbose_name 1 %}

.. autoclass:: {{ opt.app_label }}.models.{{ opt.object_name }}
    :members:

.. list-table::
    :header-rows: 1

    *   - {% trans 'Field Name' %}
        - {% trans 'Field Verbose Name' %}
        - {% trans 'Field DB Type' %}
        - {% trans 'Field Description' %}

{% for field in opt.fields %}
    *   - {{ field.name }}
        - {{ field.verbose_name }} 
        - {{ field|db_type:connection }} 
        - {{ field.help_text }} 
          {% if field.choices %}
          .. list-table::
                :header-rows: 1

                *   - {% trans 'Option Value' %}
                    - {% trans 'Option Label' %}

                {% for choice in field.choices %}
                *   - {{ choice.0 }}
                    - {{ choice.1 }}
                {% endfor %}

         {% endif %}
{% endfor %}{# field #}

{% if subdoc %}
.. include:: {{ opt.app_label }}.models.{{ opt.object_name }}.rst
{% endif %}

{% endfor %}{# model #}
