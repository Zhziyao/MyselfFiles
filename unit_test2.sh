#!/bin/bash

function print_help()
{
    echo "Use md5 to test the validity of libyami codec"
    echo "# Examples of usage:"
    echo "unit_test.sh  --encode"
    echo "              AVC(HEVC|AVC|VP8|JPEG)"
    echo "              I420(I420|NV12)"
    echo "              /path(source YUV file directory)"
    echo "              1(1|0, save or not save compressed file)"
    echo "              /path(save directory)"
    echo
    echo "unit_test.sh  --decode"
    echo "              framesNumber(the number of decoding frames, -1 stands for the entire file)"
    echo "              /path(source file directory)"
    echo "              1(1|0, save or not save YUV file)"
    echo "              /path(save directory)"
    echo
    echo "unit_test.sh  decode"
    echo "              /path(source file directory)"
    echo "              /path(save yuv directory)"
    echo
    exit 0
}


function check_log()
{
    rm -rf ${outputpath}
    mkdir -p ${outputpath}
    tmpfail=${outputpath}/fail.result
    tmpass=${outputpath}/pass.result
    if [ ! -d ${scriptpath}/log ]; then
        mkdir ${scriptpath}/log
    fi
    touch ${logfile}
}


function check_path()
{
    local save=$1

    if [ -d $filepath ]; then
        filepath=$(cd "$filepath"; pwd)/
    elif [ -f $filepath ]; then
        local filename=${filepath##*/}
        local path=${filepath%/*}
        filepath=$(cd "$path"; pwd)/
    else
        error_msg "please check source directory, $filepath"
    fi

    if [ $save -eq 1 ]&&[ -z "$savepath" ]; then
        error_msg "please provide save directory, $savepath"
    fi

    if [ $save -eq 0 ]; then
        savepath=${outputpath}
    fi

    if [ -d $savepath ]; then
        savepath=$(cd "$savepath"; pwd)/
    else
        mkdir $savepath
        if [ $? -ne 0 ]; then
            error_msg "please check save directory, $savepath"
        fi
        savepath=$(cd "$savepath"; pwd)/
    fi

    rm -rf  ${savepath}*
}

function error_msg()
{
    echo
    echo "********Arguments Error*********"
    echo $1
    echo
    if [ $2 ]; then
        print_help
    else
        exit 1
    fi
}

function write_log()
{
    echo "unit test result:" >> ${logfile}
    local passfile=$[filenumber - failnumber]
    echo "opened files:${filenumber}, passed files:${passfile}, failed files:${failnumber}" >> ${logfile}
    if [ -f ${tmpfail} ]; then
        cat ${tmpfail} >> ${logfile}
        echo >> ${logfile}
    fi
    if [ -f ${tmpass} ]; then
        cat ${tmpass}  >> ${logfile}
    fi
}


function verify_md5()
{
    local bits=$1
    local filename=$2
    local save=$3
    local filepath1=$4

    if [ ! -f ${bits} ]; then
        echo "${bits} not exists, please check it"
        exit 0
    fi

    local refmd5=`awk '$2 ~/^'${filename}'/{print $1}' ${bits}`
    local md5=''
    if [ $save -eq 0 ]; then
        md5=`grep whole ${savepath}${filename}.md5 | awk '{print $5}'`
        rm ${savepath}${filename}".md5"
    else
        local file2=`ls -lrt ${savepath} | awk 'END{print $NF}'`
        md5=`md5sum ${savepath}${file2} | awk 'END{print $1}'`
    fi
    if [ $refmd5 ]; then
        if [ "X$refmd5" == "X$md5" ]; then
            echo -e "${filepath1}${filename} pass" >> ${tmpass}
        else
            echo -e "${filepath1}${filename} fail"  >> ${tmpfail}
            failnumber=$[failnumber + 1]
            if [ $save -eq 1 ]; then
                rm ${savepath}${file2}
            fi
        fi
    else
        echo -e "${filepath1}${filename} No MD5 fail" >> ${tmpfail}
        failnumber=$[failnumber + 1]
        if [ $save -eq 1 ]; then
            rm ${savepath}${file2}
        fi
    fi
}

function do_decode()
{
    local filepath1=$1
    local save=$2
    local verify=$3

    local bits=${filepath1}bits.md5
    local number=`ls -l $filepath1 | grep "^-" | wc -l`
    number=$[number -1]
    filenumber=$[filenumber + number]

    local mode=0
    if [ $save -eq 0 ];then
        mode=-2
    else
        mode=0
    fi

    local files=`ls $filepath1`
    for file in $files
    do
        if [ $file = "bits.md5" ]; then
            continue
        fi

        local file2=${filepath1}${file}
        if [ -d ${file2} ]; then
            do_decode ${file2}/  $save  $verify
        else
            echo $file2
            run_Cmd="${decode} -w 0 -n ${decodeframes} -i ${file2} -m ${mode} -o ${savepath}"
            echo $run_Cmd >> /home/snow/decodeCmd.txt
            ${decode} -w 0 -n ${decodeframes} -i ${file2} -m ${mode} -o ${savepath}
            if [ $? -eq 0 ]; then
                if [ $verify -eq 1 ]; then
                    verify_md5 ${bits} ${file} $save ${filepath1}
                fi
            else
                echo -e "${file2} fail"  >> ${tmpfail}
                failnumber=$[failnumber + 1]
            fi
        fi
    done
}


function decode()
{
    if [ $# -ne 4 -a $# -ne 3 ]; then
        error_msg "please according to the message, check the arguments"  1
    fi

    filepath=$1
    local verify=$2
    local save=$3
    savepath=$4

    check_log

    check_path $save

    do_decode $filepath $save $verify

    write_log
}

function get_resolution()
{
    local fileyuv=$1
    #local file1=${fileyuv##*_}
    local file1=${fileyuv%%_*}
    #local file2=${file1%.*}
    WIDTH=${file1%x*}
    HEIGHT=${file1#*x}
}

function verify_encode()
{
    local sYuvfile=$1
    local dfile=$2

    ${decode} -m 0 -i $dfile -o ${outputpath} -f I420

    if [ $? -ne 0 ];then
        echo -e "${dfile} decode fail"  >> ${tmpfail}
        failnumber=$[failnumber + 1]
        return
    fi

    local dYuvfile=`ls -lrt ${outputpath} | awk 'END{print $NF}'`

    ${scriptpath}/psnr -i ${sYuvfile} -o ${outputpath}${dYuvfile} -W $WIDTH -H $HEIGHT -s $encodepsnr
    rm  ${outputpath}${dYuvfile}
}

function psnr_result()
{
    local psnr_result="${scriptpath}/average_psnr.txt"
    if [ -f $psnr_result ];then
        local passcount=`grep "pass" ${psnr_result} | wc -l `
        failnumber=$[filenumber - passcount]
        cat ${psnr_result} | while read line;
        do
            local pass=`echo ${line:(-4)}`
            if [ "X$pass" == "Xpass" ];then
                echo -e "$line" >> ${tmpass}
            else
                echo -e "$line" >> ${tmpfail}
            fi
        done
    else
        echo "${psnr_result} not exists" >> ${tmpfail}
    fi
}

function do_encode()
{
    local codec=$1
    local fourcc=$2
    local filepath1=$3
    local save=$4
    local ipperiod=$5

    local number=`ls -l $filepath1 | grep "^-" | wc -l`
    filenumber=$[filenumber + number]

    local files=`ls $filepath1`
    for file in $files
    do
        local file2=${filepath1}${file}
        local file3=${savepath}${file}.${suffix[$codec]}
        if [ -d ${file2} ]; then
            do_encode $codec $fourcc ${file2}/ $save
        else
            get_resolution $file
            run_cmd="${encode} -i ${file2} -W ${WIDTH} -H ${HEIGHT} -c $codec -s $fourcc -o ${file3}"
            if [ ${ipperiod} -gt 1 ];then
                run_cmd="${run_cmd} --ipperiod ${ipperiod}"
            fi
            #echo "encode: $file2"
            echo "encode: ${run_cmd}"
            ########################Get Cmd.
            echo "encode: ${run_cmd}" >> /home/snow/encodeCmd.txt
            ${run_cmd}
            if [ $? -eq 0 ];then
                verify_encode ${file2} ${file3}
            else
                echo -e "${file2} fail"  >> ${tmpfail}
                failnumber=$[failnumber + 1]
            fi
            if [ $save -eq 0 ];then
                rm ${file3}
            fi
        fi
    done
}


function encode()
{
    if [ $# -ne 5 -a $# -ne 4 ];then
        error_msg "please according to the message, check the args"  1
    fi

    local codec=''
    local fourcc=$2
    local save=$5
    local ipperiod=$4
    filepath=$3
    savepath=$6

    local codes="HEVC AVC VP8 VP9 JPEG"
    for cds in $codes
    do
        if [ $1 = $cds ];then
            codec=$1
            break
        fi
    done

    if [ -z $codec ];then
        error_msg "not support codec, $1" 1
    fi

    #if [ $codec = 'JPEG' ];then
    #    decode=$jpegDecoder
    #fi

    if [ "X$fourcc" != "XI420" -a "X$fourcc" != "XNV12" ];then
        error_msg "not support fourcc: $fourcc" 1
    fi

    if [ -f ${scriptpath}/average_psnr.txt ];then
        rm ${scriptpath}/average_psnr.txt
    fi

    check_log

    check_path $save

    do_encode $codec $fourcc $filepath $save $ipperiod

    psnr_result

    write_log
}


function encode_performance_test()
{
    local codec=$1
    local inputfile=$2
    local outputdir=$3
    local outputfilename=$4
    local save=$5
    local logfilename=""
    local cmd=""
    local result=0

    if [ -d $outputdir ]; then
        echo "$outputdir exist"
    else
	    mkdir $outputdir
    fi
    outputfile="$outputdir/$outputfilename"
    logfilename=${outputfile}.log
    if [ -f ${outputfile} ]; then
        rm -rf ${outputfile}
        echo "${outputfile} exist, removed."
    fi
    if [ -f ${logfilename} ]; then
        rm -rf ${logfilename}
        echo "${logfilename} exist, removed."
    fi

    get_resolution $inputfile

    DateValue=`date +%Y-%m-%d-%H-%M-%S`
    echo ${DateValue} >${logfilename}
    #echo "${yamitranscode} -i ${inputfile}  -W ${WIDTH} -H ${HEIGHT} -N 1000  --ipperiod 3 --rcmode CBR -b 4096  -o ${outputfile} >>${logfilename} "
    if [ $codec = "HEVC" ];then
        ${yamitranscode} -i ${inputfile} -W ${WIDTH} -H ${HEIGHT} -N 1000 --intraperiod=32  --rcmode=CBR  -b 2048  -o ${outputfile} >>${logfilename}
        result=$?
    fi
    if [ $codec = "AVC" ];then
        ${yamitranscode} -i ${inputfile}  -W ${WIDTH} -H ${HEIGHT} -N 1000 --intraperiod=32  --ipperiod=3  --rcmode=CBR -b 4096  -o ${outputfile} >>${logfilename}
        result=$?
    fi
    #${yamitranscode} -i ${inputfile}  -W ${WIDTH} -H ${HEIGHT} -N 1000  --ipperiod 3 --rcmode CBR -b 4096  -o ${outputfile} >>${logfilename}
    #${yamitranscode} -i ${inputfile} -W ${WIDTH} -H ${HEIGHT} -N 1000  -o ${outputfile} >>${logfilename}
    if [ $result -eq 0 ];then
      echo -e "${outputfilename} transcode success"  >>${logfilename}
    else
      echo -e "${outputfilename} transcode fail"  >>${logfilename}
    fi
}


scriptpath=$(cd "$(dirname "$0")"; pwd)
DAY=`date +%Y-%m-%d-%H-%M-%S`
logfilename="test_result-"${DAY}".log"
logfile=${scriptpath}/log/${logfilename}

decodeframes=-1
decode=${scriptpath%/*}/tests/yamidecode
encode=${scriptpath%/*}/tests/yamiencode
yamitranscode=${scriptpath%/*}/tests/yamitranscode
#jpegDecoder=/home/regression/Installation/relicense/libyami/bin/yamidecode
encodepsnr=33

outputpath="${scriptpath}/yuv/"
tmpass=''
tmpfail=''

failnumber=0
filenumber=0

filepath=''
savepath=''

declare -A suffix
suffix=([AVC]=264 [HEVC]=265 [VP8]=vp8 [VP9]=vp9 [JPEG]=jpg)

if [ $1 ] && [ $1 = "--decode" ]; then
    decodeframes=$2
    if [ $2 -lt 0 ]; then
        decodeframes=-1
    fi
    decode $3 1 $4 $5
    cat ${logfile}
elif [ $1 ] && [ $1 = "--encode" ]; then
    encode  $2 $3 $4 $5 $6 $7
    cat ${logfile}
elif [ $1 ] && [ $1 = "decode" ]; then
    decode $2 0 1 $3
elif [ $1 ] && [ $1 = "--encode-performance" ]; then
    encode_performance_test $2 $3 $4 $5 $6 
else
    print_help
fi
