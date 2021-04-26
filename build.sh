app='TA-strava-for-splunk'
build_folder='build_files'
dir=.

version=$(cat ${dir}/default/app.conf | grep version | grep -o '.....$')

rm -rf .git*
rm -f requirements.txt

# Get latest version of spl from pre-mod directory and extract to current folder
#filename=$(ls -t pre-mod/* | head -1)
#tar xvzf $filename

# Inserts the helplinks.js line before </body>
sed -i'' 's#<\/body.*#<script src="${make_url(app_js + '\''/helplinks.js'\'')}"></script></body>#' ${dir}/appserver/templates/base.html 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Adding custom JS file to base.html : SUCCESS"
else
    echo "- Adding custom JS file to base.html : FAIL"
fi

# Adds KV_MODE = none to [strava:activities] stanza in props.conf, using gsed. Required as AOB strips it, which is a bug.
#sed -i'' '/^\[strava:activities\]/a KV_MODE = none' ${dir}/default/props.conf 2>/dev/null
#if [ $? -eq 0 ]; then
#    echo "- Adding 'KV_MODE = none' to [strava:activities] stanza in props.conf : SUCCESS"
#else
#    echo "- Adding 'KV_MODE = none' to [strava:activities] stanza in props.conf : FAIL"
#fi


cp ${build_folder}/globalConfig.json ${dir}/appserver/static/js/build/globalConfig.json 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Replacing globalConfig.json with new version : SUCCESS"
else
    echo "- Replacing globalConfig.json with new version : FAIL"
fi

sed -i'' 's/APP_VERSION/'${version}'/' ${dir}/appserver/static/js/build/globalConfig.json 2>/dev/null

# Replace bootstrap-enterprise.css with stock Splunk 8.x one for new fonts:
cp ${build_folder}/bootstrap-enterprise.css ${dir}/appserver/static/css/bootstrap-enterprise.css 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Replacing bootstrap-enterprise.css to use new Splunk fonts : SUCCESS"
else
    echo "- Replacing bootstrap-enterprise.css to use new Splunk fonts : FAIL"
fi

# Replace common.css with stock Splunk 8.x one for new fonts:
cp ${dir}/${build_folder}/common.css ${dir}/appserver/static/css/common.css 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Replacing common.css to update UI elements : SUCCESS"
else
    echo "- Replacing common.css to update UI elements : FAIL"
fi

# Updates appserver/static/js/build/common.js to make it look more like a modern Splunk UI
sed -i'' 's/font-size:12px;font-family:Roboto,Droid,Helvetica Neue,Helvetica,Arial,sans-serif/font-size:14px;font-family:Splunk Platform Sans,Proxima Nova,Roboto,Droid,Helvetica Neue,Helvetica,Arial,sans-serif/g' ${dir}/appserver/static/js/build/common.js 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Updating common.js to be inline with new Splunk UI (1/2) : SUCCESS"
else
    echo "- Updating common.js to be inline with new Splunk UI (1/2) : FAIL"
fi

# Second pass for when font-size is not specified before font-family.
sed -i'' 's/font-family:Roboto,Droid,Helvetica Neue,Helvetica,Arial,sans-serif/font-family:Splunk Platform Sans,Proxima Nova,Roboto,Droid,Helvetica Neue,Helvetica,Arial,sans-serif/g' ${dir}/appserver/static/js/build/common.js 2>/dev/null
if [ $? -eq 0 ]; then
    echo "- Updating common.js to be inline with new Splunk UI (2/2) : SUCCESS"
else
    echo "- Updating common.js to be inline with new Splunk UI (2/2) : FAIL"
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
    echo "- Replacing ${dir}/default/data/ui/nav/default.xml : SUCCESS"
else
    echo "- Replacing ${dir}/default/data/ui/nav/default.xml : FAIL"
fi

# Remove ${build_folder} and build script so it doesn't end up in tgz file
rm -rf ${dir}/${build_folder}
rm -rf ${dir}/build.sh

find ${dir} -type f -print0 | xargs -0 chmod 0644
find ${dir}/bin -type f -print0 | xargs -0 chmod 0755
find ${dir} -type d -print0 | xargs -0 chmod 0755

# Get app version, set date and create file in /tmp folder
version=$(cat ${dir}/default/app.conf | grep version | grep -o '.....$')
if [ $? -eq 0 ]; then
    #datetime=$(date +%F_%H-%M-%S)
    ls -lah 
    cd ${dir}/..
    filename="${app}.tgz"
    #filename="${app}_${version}.tgz"

    # Now package it all into a tar.gz that can be uploaded to Splunkbase
    COPYFILE_DISABLE=1 tar zcf ${filename} --exclude-vcs ${app} 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "- Final app is ${filename} in $PWD: SUCCESS"
        mv ${filename} ${app}
    else
        echo "- Final app is ${filename} in $PWD: FAIL"
        ls -lah
    fi
else
    echo "Error reading app.conf, is app location correct? : FAIL"
fi

# Delete the $app folder
#rm -rf ${dir}
#if [ $? -eq 0 ]; then
#    echo "- Removing temporary ${app} folder : SUCCESS"
#else
#    echo "- Removing temporary ${app} folder : FAIL"
#fi