Name: 		pbis-open-upgrade
Summary: 	Upgrade helper package for PowerBroker Identity Services Open
Version: 	8.2.2
Release:	3
License: 	GPLv2
URL: 		http://www.beyondtrust.com/Products/PowerBroker-Identity-Services-Open-Edition/
Obsoletes: likewise-open-upgrade, likewise-open, likewise-srvsvc, likewise-base, likewise-base-32bit, likewise-domainjoin, likewise-domainjoin-gui, likewise-eventfwd, likewise-eventlog, likewise-grouppolicy, likewise-grouppolicy-32bit, likewise-krb5, likewise-libxml2, likewise-lsass, likewise-lsass-32bit, likewise-lsass-enterprise, likewise-lwadtool, likewise-lwadutil, likewise-lwconfig, likewise-lwio, likewise-lwnetapi, likewise-lwreskit, likewise-lwtools, likewise-lwreg, likewise-lwupgrade, likewise-mod-auth-kerb, likewise-netlogon, likewise-openldap, likewise-passwd, likewise-pstore, likewise-reapsysl, likewise-reskit, likewise-rpc, likewise-samba-interop, likewise-smartcard, likewise-smartcard-32bit, likewise-sqlite, likewise-lwreg-32bit
Requires: grep, sh-utils
Requires: xenserver-active-directory
AutoReq: no

%description
PowerBroker Identity Services provides Active Directory authentication.

%pre
UPGRADEDIR=/var/lib/pbis-upgrade

LOG=/var/log/pbis-open-install.log

DAEMONS_TO_HALT="reapsysld lsassd lwiod netlogond dcerpcd eventlogd lwregd lwsmd"

# Display to screen and log file with a blank line between entries.
log()
{
    echo $@
    echo
    echo $@ >> $LOG
    echo >> $LOG
}

# Display to screen and log file with no blank line.
_log()
{
    echo $@
    echo $@ >> $LOG
}

# Display to file.
logfile()
{
    echo $@ >> $LOG
    echo >> $LOG
}

# Execute command.
# If successful, note in log file.
# If not successful, note on screen and log file.
run()
{
    tlog=$("$@" 2>&1)
    err=$?
    if [ $err -eq 0 ]; then
        echo "Success: $@" >> $LOG
        echo "$tlog" >> $LOG
        echo >> $LOG
    else
        _log "Error: $@ returned $err"
        _log "$tlog"
        _log
    fi
    return $err
}

# Execute command.
# Log only to file.
run_quiet()
{
    tlog=$("$@" 2>&1)
    err=$?
    if [ $err -eq 0 ]; then
        echo "Success: $@" >> $LOG
    else
        echo "Error: $@ returned $err  (ignoring and continuing)" >> $LOG
    fi
    echo "$tlog" >> $LOG
    echo >> $LOG
    return $err
}

# Execute command.
# If successful, note in log file.
# If not successful, note on screen and log file and then exit.
run_or_fail()
{
    tlog=$("$@" 2>&1)
    err=$?
    if [ $err -eq 0 ]; then
        echo "Success: $@" >> $LOG
        echo "$tlog" >> $LOG
        echo >> $LOG
    else
        _log "Error: $@ returned $err  (aborting this script)"
        _log "$tlog"
        _log
        exit 1
    fi
    return $err
}

determine_upgrade_type()
{
    LW_VERSIONFILE=/opt/likewise/data/VERSION
    LW_ENTERPRISE_VERSIONFILE=/opt/likewise/data/ENTERPRISE_VERSION
    VERSIONFILE=/opt/pbis/data/VERSION
    ENTERPRISE_VERSIONFILE=/opt/pbis/data/ENTERPRISE_VERSION

    if [ -f "$ENTERPRISE_VERSIONFILE" ]; then
        log "$ENTERPRISE_VERSIONFILE exists: Uninstall PowerBroker Identity Services Enterprise before proceeding."
#        exit 1
    elif [ -f "/opt/pbis/sbin/gpagentd" ]; then
        log "/opt/pbis/sbin/gpagentd exists: Uninstall PowerBroker Identity Services Enterprise before proceeding."
#        exit 1
    elif [ -f "$LW_ENTERPRISE_VERSIONFILE" ]; then
        log "$LW_ENTERPRISE_VERSIONFILE exists: Uninstall Likewise Enterprise before proceeding."
#        exit 1
    elif [ -f "/opt/likewise/sbin/gpagentd" ]; then
        log "/opt/likewise/sbin/gpagentd exists: Uninstall Likewise Enterprise before proceeding."
#        exit 1
    fi

    if [ -f "$LW_VERSIONFILE" ]; then
        run_or_fail mkdir -p "${UPGRADEDIR}"
        run_or_fail cp "$LW_VERSIONFILE" "${UPGRADEDIR}"

        run_or_fail cat "$LW_VERSIONFILE"
        if [ -n "`grep '^VERSION=5.0' $LW_VERSIONFILE`" ]; then
            UPGRADING_FROM_5_0123=1
            log "Preserving Likewise Identity Services Open 5.0 configuration in ${UPGRADEDIR}."
        elif [ -n "`grep '^VERSION=5.1' $LW_VERSIONFILE`" ]; then
            UPGRADING_FROM_5_0123=1
            log "Preserving Likewise Identity Services Open 5.1 configuration in ${UPGRADEDIR}."
        elif [ -n "`grep '^VERSION=5.2' $LW_VERSIONFILE`" ]; then
            UPGRADING_FROM_5_0123=1
            log "Preserving Likewise Identity Services Open 5.2 configuration in ${UPGRADEDIR}."
        elif [ -n "`grep '^VERSION=5.3' $LW_VERSIONFILE`" ]; then
            UPGRADING_FROM_5_0123=1
            log "Preserving Likewise Identity Services Open 5.3 configuration in ${UPGRADEDIR}."
        elif [ -n "`grep '^VERSION=6.0' $LW_VERSIONFILE`" ]; then
            UPGRADING_FROM_6_0=1
            log "Preserving Likewise Open 6.0 configuration in ${UPGRADEDIR}."
        elif [ -n "`grep '^VERSION=6.1' $LW_VERSIONFILE`" ]; then
            UPGRADING_FROM_6_1=1
            log "Preserving Likewise Open 6.1 configuration in ${UPGRADEDIR}."
        fi
    elif [ -f "$VERSIONFILE" ]; then
        run_or_fail mkdir -p "${UPGRADEDIR}"
        run_or_fail cp "$VERSIONFILE" "${UPGRADEDIR}"

        UPGRADING_PBIS=1

        run_or_fail cat "$VERSIONFILE"
        if [ -n "`grep '^VERSION=6.5' $VERSIONFILE`" ]; then
            UPGRADING_FROM_6_5=1
            log "Upgrading PowerBroker Identity Services Open 6.5."
        elif [ -n "`grep '^VERSION=7.0' $VERSIONFILE`" ]; then
            UPGRADING_FROM_7_0=1
            log "Upgrading PowerBroker Identity Services Open 7.0."
        elif [ -n "`grep '^VERSION=7.1' $VERSIONFILE`" ]; then
            UPGRADING_FROM_7_1=1
            log "Upgrading PowerBroker Identity Services Open 7.1."
        fi
    fi
}

determine_join_status()
{
    if [ -n "$UPGRADING_FROM_5_0123" ]; then
        domain=`/opt/likewise/bin/lw-get-current-domain 2>/dev/null | sed -e 's/^Current Domain = //'`
        if [ -n "$domain" ]; then
            logfile "System is joined to $domain according to lw-get-current-domain"
            STATUS_JOINED=$domain
        else
            logfile "System does not appear to be joined according to lw-get-current-domain"
        fi
    elif [ -n "$UPGRADING_FROM_6_0" -o -n "$UPGRADING_FROM_6_1" ]; then
        domain=`/opt/likewise/bin/lw-lsa ad-get-machine account 2>/dev/null | grep '  DNS Domain Name: ' | sed -e 's/  DNS Domain Name: //'`
        if [ -n "$domain" ]; then
            logfile "System is joined to $domain according to lw-lsa ad-get-machine account"
            STATUS_JOINED=$domain
        else
            logfile "System does not appear to be joined according to lw-lsa ad-get-machine account"
        fi
    elif [ -n "$UPGRADING_PBIS" ]; then
        domain=`/opt/pbis/bin/lsa ad-get-machine account 2>/dev/null | grep '  DNS Domain Name: ' | sed -e 's/  DNS Domain Name: //'`
        if [ -n "$domain" ]; then
            logfile "System is joined to $domain according to lsa ad-get-machine account"
            STATUS_JOINED=$domain
        else
            logfile "System does not appear to be joined according to lsa ad-get-machine account"
        fi
    fi
}

set_UnixLastChangeTime()
{
    if [ -d /opt/pbis/bin ]; then
        regshell=/opt/pbis/bin/regshell
    elif [ -d /opt/likewise/bin ]; then
        regshell=/opt/likewise/bin/lwregshell
    else
        regshell=/usr/bin/lwregshell
    fi

    if [ -n "$STATUS_JOINED" ]; then
        if [ -n "$UPGRADING_FROM_6_0" ]; then
            run_quiet $regshell set_value '[HKEY_THIS_MACHINE\Services\lsass\Parameters\Providers\ActiveDirectory\Pstore\Default]' 'ClientModifyTimestamp' '0'
        elif [ -n "$UPGRADING_FROM_6_1" -o -n "$UPGRADING_PBIS" ]; then
            domain_list=`$regshell list_keys '[HKEY_THIS_MACHINE\Services\lsass\Parameters\Providers\ActiveDirectory\DomainJoin]'`
            for KEYS in $domain_list
            do
                domain=`echo $KEYS | tr -d ']'`
                run_quiet $regshell set_value "$domain\Pstore]" 'UnixLastChangeTime' '0'
            done
        fi
    fi
}

add_TrustEnumerationWaitSetting()
{
    if [ -d /opt/pbis/bin ]; then
        regshell=/opt/pbis/bin/regshell
    elif [ -d /opt/likewise/bin ]; then
        regshell=/opt/likewise/bin/lwregshell
    else
        regshell=/usr/bin/lwregshell
    fi
    if [ -n "$STATUS_JOINED" ]; then
         if [ -n "$UPGRADING_FROM_6_1" -o -n "$UPGRADING_PBIS" ]; then
            domain_list=`$regshell list_keys '[HKEY_THIS_MACHINE\Services\lsass\Parameters\Providers\ActiveDirectory\DomainJoin]'`
            for KEYS in $domain_list
            do
                run_quiet $regshell add_value "$KEYS" "TrustEnumerationWait" "REG_DWORD" '0'
                run_quiet $regshell add_value "$KEYS" "TrustEnumerationWaitSeconds" "REG_DWORD" '0'
            done
         fi
    fi
}

preserve_join_status()
{
    if [ -n "$STATUS_JOINED" ]; then
        logfile "Saving STATUS_JOINED=$STATUS_JOINED"
        echo "STATUS_JOINED=$STATUS_JOINED" >> "${UPGRADEDIR}/status.txt"
    fi
}

preserve_5_0123_configuration()
{
    if [ -n "${UPGRADING_FROM_5_0123}" ]; then
        if [ -f "/etc/likewise/eventlogd.conf" ]; then
            run_or_fail cp /etc/likewise/eventlogd.conf "${UPGRADEDIR}"
        fi

        if [ -f "/etc/likewise/lsassd.conf" ]; then
            run_or_fail cp /etc/likewise/lsassd.conf "${UPGRADEDIR}"
        fi

        if [ -f "/etc/likewise/netlogon.conf" ]; then
            run_or_fail cp /etc/likewise/netlogon.conf "${UPGRADEDIR}"
        fi

        if [ -f "/var/lib/likewise/db/pstore.db" ]; then
            run_or_fail cp /var/lib/likewise/db/pstore.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/pstore.db"
        fi
    fi
}

preserve_6_0_configuration()
{
    if [ -n "${UPGRADING_FROM_6_0}" ]; then
        if [ -f "/var/lib/likewise/db/registry.db" ]; then
            run_or_fail cp /var/lib/likewise/db/registry.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/registry.db"
        fi

        if [ -f "/var/lib/likewise/db/sam.db" ]; then
            run_or_fail cp /var/lib/likewise/db/sam.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/sam.db"
        fi

        if [ -f "/var/lib/likewise/db/lwi_events.db" ]; then
            run_or_fail cp /var/lib/likewise/db/lwi_events.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/lwi_events.db"
        fi

        if [ -f "/var/lib/likewise/db/lsass-adcache.db" ]; then
            run_or_fail cp /var/lib/likewise/db/lsass-adcache.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/lsass-adcache.db"
        fi

        if [ -f "/var/lib/likewise/db/lsass-adcache.filedb" ]; then
            run_or_fail cp /var/lib/likewise/db/lsass-adcache.filedb "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/lsass-adcache.filedb"
        fi
    fi
}

preserve_6_1_configuration()
{
    if [ -n "${UPGRADING_FROM_6_1}" ]; then
        if [ -f "/var/lib/likewise/db/registry.db" ]; then
            run_or_fail cp /var/lib/likewise/db/registry.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/registry.db"
        fi

        if [ -f "/var/lib/likewise/db/sam.db" ]; then
            run_or_fail cp /var/lib/likewise/db/sam.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/sam.db"
        fi

        if [ -f "/var/lib/likewise/db/lwi_events.db" ]; then
            run_or_fail cp /var/lib/likewise/db/lwi_events.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/lwi_events.db"
        fi

        if [ -f "/var/lib/likewise/db/lsass-adcache.db" ]; then
            run_or_fail cp /var/lib/likewise/db/lsass-adcache.db "${UPGRADEDIR}"
            run_or_fail chmod 700 "${UPGRADEDIR}/lsass-adcache.db"
        fi

        for cache in /var/lib/likewise/db/lsass-adcache.filedb.* ; do
            if [ -f "$cache" ]; then
                cachefile=`basename $cache`
                run_or_fail cp "${cache}" "${UPGRADEDIR}"
                run_or_fail chmod 700 "${UPGRADEDIR}/${cachefile}"
            fi
        done
    fi
}

wait_for_lwsm_shutdown()
{
    LWSMD_WAIT_TIME=$1

    while [ "$LWSMD_WAIT_TIME" -ne 0 ]; do
        sleep 1
        run_quiet '/opt/pbis/bin/lwsm' list
        if [ $? -ne 0 ]; then
            return 0
        fi
        LWSMD_WAIT_TIME=`expr $LWSMD_WAIT_TIME - 1`
    done

    return 1
}

preinstall()
{
    logfile "Package: PowerBroker Identity Services Open Upgrade begins (`date`)"

    determine_upgrade_type

    determine_join_status

    set_UnixLastChangeTime

    add_TrustEnumerationWaitSetting

    # CA-261195 We never enable the full pam configuration for pbis, as we don't
    # need it, as such we shouldn't need to disable it. Doing so requires us to
    # re-enable it, and re-enabling it in its entirety brings about CA-211425.
    # We could in theory safely disable and re-enable nsswitch, but as all the
    # logic to do the --enable is block disabled in this file (instead relying
    # on a first boot script), it's  simplest just to refuse to disable it here.
    if false && [ -x /opt/pbis/bin/domainjoin-cli ]; then
        run_quiet '/opt/pbis/bin/domainjoin-cli' configure --disable pam
        run_quiet '/opt/pbis/bin/domainjoin-cli' configure --disable nsswitch

    elif false && [ -x /opt/likewise/bin/domainjoin-cli ]; then
        run_quiet /opt/likewise/bin/domainjoin-cli configure --disable pam
        run_quiet /opt/likewise/bin/domainjoin-cli configure --disable nsswitch
    fi

    if [ -x /etc/init.d/likewise ]; then
        run_quiet /etc/init.d/likewise stop
    fi

    if [ -x /etc/init.d/pbis ]; then
        run_quiet /etc/init.d/pbis stop
    fi

    if [ -x /etc/init.d/lwsmd ]; then
        run_quiet /etc/init.d/lwsmd stop
    fi

    if [ -x /opt/pbis/bin/lwsm ]; then
        run_quiet '/opt/pbis/bin/lwsm' shutdown
        wait_for_lwsm_shutdown 60
    fi
    for daemon in $DAEMONS_TO_HALT; do
        if [ -x /etc/rc.d/$daemon ]; then
            run_quiet /etc/rc.d/$daemon stop
        fi
        run_quiet pkill -KILL -x $daemon
    done

    preserve_5_0123_configuration

    preserve_6_0_configuration

    preserve_6_1_configuration

#   preserve_6_5_configuration is not needed

    preserve_join_status

    logfile "Package: PowerBroker Identity Services Open Upgrade finished"
    exit 0
}

preinstall

%files
%defattr(-,root,root)

%changelog
* Fri Jun 23 2017 Simon Rowe <simon.rowe@eu.citrix.com> - 8.2.2-2
- CA-257199: add Requires: of XS virtual package
