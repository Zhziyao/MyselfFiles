#!/bin/bash

CURRENT_PATH=`pwd`
tools=$CURRENT_PATH/medias_for_verify/media_tools/ssim_op
sourceDir=$1
refDir=$2
resultFile=vc1.tmp
logfile=vc1_result.tmp
vc1_rcv_errorLog=vc1_error.tmp
frameCount=30

rm $resultFile
rm $logfile
rm $vc1_rcv_errorLog

filenumber=`ls -l $sourceDir | grep "^-" | wc -l`
failnumber=0

function help()
{
	echo
	echo "./vc1_rcv_verify.sh  /path(yami decoded yuv)"
	echo '		/path(reference yuv)'
	echo
	exit 1
}

function get_resolution()
{
    local fileyuv=$1
    local file1=${fileyuv##*_}
    local file2=${file1%.*}
    WIDTH=${file2%x*}
    HEIGHT=${file2#*x}
}

function write_log()
{
    echo "unit test result:" >> ${logfile}
    local passfile=$[filenumber - failnumber]
    echo "opened files:${filenumber}, passed files:${passfile}, failed files:${failnumber}" >> ${logfile}
    if [ -f ${vc1_rcv_errorLog} ]; then
        cat ${vc1_rcv_errorLog} >> ${logfile}
        echo >> ${logfile}
    fi
    cat ${logfile}
}

function writelog()
{
	local fileName=$1
	local y_min=`grep Y_MIN_SSIM  $resultFile | awk '{print $3}'`
	local y_average=`grep Y_AVERAGE_SSIM  $resultFile | awk '{print $3}'`
	local u_min=`grep U_MIN_SSIM  $resultFile | awk '{print $3}'`
	local u_average=`grep U_AVERAGE_SSIM  $resultFile | awk '{print $3}'`
	local v_min=`grep V_MIN_SSIM  $resultFile | awk '{print $3}'`
	local v_average=`grep V_AVERAGE_SSIM  $resultFile | awk '{print $3}'`

	local result=0
	if [ $(echo "$y_min < 0.99"|bc) -eq 1 ]; then
		result=1
	fi
	if [ $(echo "$u_min < 0.99"|bc) -eq 1 ]; then
		result=1
	fi
	if [ $(echo "$v_min < 0.99"|bc) -eq 1 ]; then
		result=1
	fi

	if [ $result -eq 1 ]; then
		failnumber=$[failnumber + 1]
		echo -e "$fileName Y_MIN:$y_min U_MIN:$u_min V_MIN:$v_min fail \n" >> $vc1_rcv_errorLog
	fi
}

if [ $1 ] && [ $1 = '-h' ]; then
	help
fi 

for file in `ls $sourceDir`
do
	get_resolution $file
	fileName=${file%_*}
	refYuv=${fileName}.yuv
	echo $file
    echo "wdp tools: $tools"
	$tools $WIDTH $HEIGHT $frameCount 0 0 ${sourceDir}/${file} ${refDir}/${refYuv}  2>error.tmp  >$resultFile
	writelog $fileName
done

write_log
