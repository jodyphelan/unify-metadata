# unify-metadata

This package helps with merging metadata from different sources into a single unified format.
It helps to remove some of the frustration involved with having the same columns and values named differently in multiple files.

## Install

```
pip3 install git+https://github.com/jodyphelan/unify-metadata.git
```

## Use

### Set up configuration file

First you have to create a yaml file (e.g. `columns.yml`) containing the columns you would like to have in your final file. 
A minimum yaml file should have an id field set. 

``` yaml
- id
```

You can also add columns which should have a specific set of values. For example we can add a column indicating phenotypic resistance to the drug rifampicin.

``` yaml
- id
- rifampicin
    values:
        - 1
        - 0
        - NA
```

We can also add a special date parser which will try to guess the date and output a user-specified format.

``` yaml
- id
- rifampicin
    values:
        - 1
        - 0
        - NA
- collection_date
    date:
        "%Y"
```

### Create a mapping file

Now we are ready to map our columns we defined to our data. You can do this by running the following command.

```
unify-metadata mappings --raw-data raw_data.csv --defaults columns.yml
```

This will create a json configuration file (default: `mapings.conf`) containing the column mappings. We can then use this file to standardise out data.

```
unify-metadata standardise --conf mappings.conf --outfile data.clean.csv --raw-data raw_data.csv
```

