app='TA-strava-for-splunk'
build_folder='build_files'
dir='/tmp/'${app}

mkdir -p ${dir}
cp -r * ${dir}/

rm -rf ${dir}/.git*
rm -rf ${dir}/bitbucket-pipelines.yml
rm -rf ${dir}/local
rm -rf ${dir}/metadata/local.meta
rm -rf ${dir}/bin/__pycache__

# Get latest version of spl from pre-mod directory and extract to current folder
#filename=$(ls -t pre-mod/* | head -1)
#tar xvzf $filename

# Inserts the helplinks.js line before </body>
gsed -i'' 's#<\/body.*#<script src="${make_url(app_js + '\''/helplinks.js'\'')}"></script></body>#' ${dir}/appserver/templates/base.html 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Adding custom JS file to base.html\t\t\t\t\t\t\tSUCCESS"
else
    echo "- Adding custom JS file to base.html\t\t\t\t\t\t\tFAIL"
fi

# Adds KV_MODE = none to [strava:activities] stanza in props.conf, using gsed. Required as AOB strips it, which is a bug.
gsed -i'' '/^\[strava:activities\]/a KV_MODE = none' ${dir}/default/props.conf 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Adding 'KV_MODE = none' to [strava:activities] stanza in props.conf\t\t\tSUCCESS"
else
    echo "- Adding 'KV_MODE = none' to [strava:activities] stanza in props.conf\t\t\tFAIL"
fi

# Replace bootstrap-enterprise.css with stock Splunk 8.x one for new fonts:
cp ${build_folder}/bootstrap-enterprise.css.newui ${dir}/appserver/static/css/bootstrap-enterprise.css 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Replacing bootstrap-enterprise.css to use new Splunk fonts\t\t\t\tSUCCESS"
else
    echo "- Replacing bootstrap-enterprise.css to use new Splunk fonts\t\t\t\tFAIL"
fi

# Replace common.css with stock Splunk 8.x one for new fonts:
cp ${dir}/${build_folder}/common.css.newui ${dir}/appserver/static/css/common.css 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Replacing common.css to update UI elements\t\t\t\t\t\tSUCCESS"
else
    echo "- Replacing common.css to update UI elements\t\t\t\t\t\tFAIL"
fi

# Updates appserver/static/js/build/common.js to make it look more like a modern Splunk UI
gsed -i'' 's/font-size:12px;font-family:Roboto,Droid,Helvetica Neue,Helvetica,Arial,sans-serif/font-size:14px;font-family:Splunk Platform Sans,Proxima Nova,Roboto,Droid,Helvetica Neue,Helvetica,Arial,sans-serif/g' ${dir}/appserver/static/js/build/common.js 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Updating common.js to be inline with new Splunk UI (1/2)\t\t\t\tSUCCESS"
else
    echo "- Updating common.js to be inline with new Splunk UI (1/2)\t\t\t\tFAIL"
fi

# # Second pass for when font-size is not specified before font-family.
gsed -i'' 's/font-family:Roboto,Droid,Helvetica Neue,Helvetica,Arial,sans-serif/font-family:Splunk Platform Sans,Proxima Nova,Roboto,Droid,Helvetica Neue,Helvetica,Arial,sans-serif/g' ${dir}/appserver/static/js/build/common.js 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Updating common.js to be inline with new Splunk UI (2/2)\t\t\t\tSUCCESS"
else
    echo "- Updating common.js to be inline with new Splunk UI (2/2)\t\t\t\tFAIL"
fi

# This overwrites the default.xml file to rearrange the order of the menu items.
cat 2>/dev/null > ${dir}/default/data/ui/nav/default.xml <<EOL
<nav search_view="search" color="#f07a35">
<view name="configuration" default="true"/>
<view name="inputs"/>
<view name="sample_dashboard" label="Sample Dashboard" />
<view name="search" label="Search"/>
</nav>
EOL
if [ $? -eq 0 ]; then
    echo "- Replacing ${dir}/default/data/ui/nav/default.xml\t\t\tSUCCESS"
else
    echo "- Replacing ${dir}/default/data/ui/nav/default.xml\t\t\tFAIL"
fi

# Remove ${build_folder} and build script so it doesn't end up in tgz file
rm -rf ${dir}/${build_folder}
rm -rf ${dir}/build_script.sh

# Get app version, set date and create file in /tmp folder
version=$(cat ${dir}/default/app.conf | grep version | grep -o '.....$')
if [ $? -eq 0 ]; then
    #datetime=$(date +%F_%H-%M-%S)
    cd ${dir}/..
    filename="${app}_${version}.tgz"

    # Now package it all into a tar.gz that can be uploaded to Splunkbase
    COPYFILE_DISABLE=1 tar zcvf ${filename} ${app} 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "- Final app is ${filename}\t\tSUCCESS"
    else
        echo "- Final app is ${filename}\t\tFAIL"
    fi
else
    echo "Error reading app.conf, is app location correct?\t\t\tFAIL"
fi

# Delete the $app folder
rm -rf ${dir}
if [ $? -eq 0 ]; then
    echo "- Removing temporary ${app} folder\t\t\t\t\tSUCCESS"
else
    echo "- Removing temporary ${app} folder\t\t\t\t\tFAIL"
fi