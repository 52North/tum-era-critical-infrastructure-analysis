#/bin/bash

echo "INPUT_HAZARD=$INPUT_HAZARD"
echo "INPUT_COUNTRY=$INPUT_COUNTRY"
echo "INPUT_INTENSITY=$INPUT_INTENSITY"
echo "OUTPUT_DAMAGE_CONSUMER_AREAS=$OUTPUT_DAMAGE_CONSUMER_AREAS"

# combine the multi-inputs to a string list
if [[ -z "${INPUT_INTENSITY}" ]]; then

    for i in {0..100}
    do
        varname="INPUT_INTENSITY_$i"

        if [[ -z "${!varname}" ]]; then
            break
        fi

        if [[ -z "${INPUT_INTENSITY}" ]]; then
            INPUT_INTENSITY="${!varname}"
        else
            INPUT_INTENSITY="$INPUT_INTENSITY,${!varname}"
        fi
        
    done
fi

echo "(combined) INPUT_INTENSITY=$INPUT_INTENSITY"

python3 ./run_analysis.py --country $INPUT_COUNTRY --hazard $INPUT_HAZARD --intensity_file $INPUT_INTENSITY --output_file $OUTPUT_DAMAGE_CONSUMER_AREAS