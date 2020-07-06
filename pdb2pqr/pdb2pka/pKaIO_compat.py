#
# $Id: pKaIO.py 432 2008-01-15 22:30:59Z nielsen $
#
# Tools for analysing pKa values and titration curves. I/O routines for the
# files from the WHAT IF pKa calculation program.
#
# Copyright (C) Jens Erik Nielsen, EMBL 2000, UCSD/HHMI 2002-2003
# University College Dublin 2003 -
# All rights reserved
#
import os
import logging
import sys
from .pKa_utility_functions_compat import getWI_resid2, reformat_name

_LOGGER = logging.getLogger(__name__)


class pKaIO:

    def __init__(self, rootfilename=None):
        self.newname = None
        self.backgr = {}
        self.desolv = {}
        self.matrix = {}
        self.pka = {}
        self.backgr_file = None
        self.desolv_file = None
        self.matrix_file = None
        self.pkafile = None
        self.titcurvfile = None
        #
        # Do we know any of the names?
        #
        if rootfilename:
            self.backgr_file = rootfilename+'.BACKGR.DAT'
            self.desolv_file = rootfilename+'.DESOLV.DAT'
            self.matrix_file = rootfilename+'.MATRIX.DAT'
            self.pkafile = rootfilename+'.PKA.DAT'
            self.titcurvfile = rootfilename+'.TITCURV.DAT'
        self.allfiles = [self.backgr_file, self.desolv_file,
                         self.matrix_file, self.pkafile, self.titcurvfile]
        #
        # Do we have the files
        #
        self.assess_status()
        #
        # Define dictionaries that we will need all the time
        #
        self.acidbase = {'ARG':1, 'HIS':1, 'LYS':1, 'TYR':-1, 'ASP':-1, 'GLU':-1,
                         'CYS':-1, 'CTERM':-1, 'NTERM':1, 'SER':-1, 'THR':-1}
        self.model_pkas = {'NTERM':8.00, 'LYS':10.40, 'GLU':4.40, 'HIS':6.30,
                           'ASP':4.00, 'TYR':9.6, 'ARG':13.0, 'CTERM':3.80,
                           'CYS':8.7, 'SER':15.0, 'THR':15.0}
        #
        # We always use the new names
        #
        self.newname = 1
        #
        # done
        #
        return

    #
    # --------------------
    #

    def assess_status(self):
        #
        # Do we have a completed pKa calculation for the PDB file?
        #
        self.file_status = {}
        self.calculation_completed = 1
        for file in self.allfiles:
            if not file:
                self.calculation_completed = None
                self.file_status[file] = None
                continue
            if os.path.isfile(file):
                self.file_status[file] = 1
            else:
                self.calculation_completed = None
                self.file_status[file] = None
        return self.calculation_completed

    #
    # -------------------------------
    #

    def readpka(self, filename=None):
        #
        # This function reads a WHAT IF pKa file and creates a dictionary with the
        # following format: self.pka={<residue1>:{'pKa':<pKa>, 'modelpK':<model pKa value>,
        # 'desolv':<dpK due to desolvation>, 'backgr':<dpK due to background int.>,
        # 'delec':<dpK due to site-site interactions>}, <residue2>:.....}
        #
        if not filename:
            filename = self.pkafile
        if not filename:
            _LOGGER.info(filename, 'is not a filename')
            sys.exit(0)
        if not os.path.isfile(filename):
            raise 'File does not exist: %s' % filename
        rfd = open(filename)
        lines = rfd.readlines()
        rfd.close()
        #
        # Parse
        #
        if lines[0].strip().lower() == 'WHAT IF pKa File'.lower():
            format_ = 'WHAT IF'
        elif lines[0].strip().lower() == 'pdb2pka pKa File'.lower():
            format_ = 'WHAT IF'
        else:
            raise ValueError('Unknown format')
        if lines[1].strip().lower() != 'Format 1.0'.lower():
            raise 'unknown format: %s' % lines[1]
        # Next line is text
        linenumber = 3
        pKa = {}
        done = None
        #
        # Define counter for keeping track of terminals
        #
        nterm = 0
        while not done:
            residue = lines[linenumber].split()
            if format_ == 'WHAT IF':
                nline = ''
                if residue[0].lower() == 'TERMINAL'.lower():
                    nterm = abs(nterm - 1)
                    nline = lines[linenumber + 1].replace('(', '')
                else:
                    nline = lines[linenumber].replace('(', '')
                nline = nline.replace(')', '')
                list_ = nline.split()
                if len(list_[3]) == 1:
                    resid = list_[2].zfill(4) + list_[1].upper() + list_[3]
                else:
                    resid = list_[2].zfill(4) + list_[1].upper()
                    chainid = None
                if residue[0].lower() == 'TERMINAL'.lower():
                    linenumber += 1
                    residue = lines[linenumber].split()
                    if len(residue[5]) == 1 and residue[5].isalpha():
                        pka = residue[6].atof()
                    else:
                        pka = residue[5].atof()
                    if len(residue) > 6:
                        if len(residue[5]) == 1 and residue[5].isalpha():
                            modelpk = residue[7].atof()
                            dpk = residue[8].atof()
                            desolv = residue[0].atof()
                            backgr = residue[10].atof()
                            site = residue[11].atof()
                        else:
                            index = 6
                            if len(residue[2]) > 1:
                                index -= 1
                            modelpk = residue[index].atof()
                            dpk = residue[index + 1].atof()
                            desolv = residue[index+2].atof()
                            backgr = residue[index+3].atof()
                            site = residue[index+4].atof()
                    else:
                        modelpk = 'Not in file'
                        dpk = 'Not in file'
                        desolv = 'Not in file'
                        backgr = 'Not in file'
                        site = 'Not in file'

                    #residue = 'T'+residue[0].zfill(4)+residue[1]
                    residue = 'T'+resid
                else:
                    if len(residue[5]) == 1 and residue[5].isalpha():
                        pka = residue[6].atof()
                    else:
                        pka = residue[5].atof()
                    #pka = residue[5].atof()
                    if len(residue) > 6:
                        if len(residue[5]) == 1 and residue[5].isalpha():
                            modelpk = residue[7].atof()
                            dpk = residue[8].atof()
                            desolv = residue[9].atof()
                            backgr = residue[10].atof()
                            site = residue[11].atof()
                        else:
                            index = 6
                            if len(residue[2]) > 1:
                                index -= 1
                            modelpk = residue[index].atof()
                            dpk = residue[index + 1].atof()
                            desolv = residue[index+2].atof()
                            backgr = residue[index+3].atof()
                            site = residue[index+4].atof()
                    else:
                        modelpk = 'Not in file'
                        dpk = 'Not in file'
                        desolv = 'Not in file'
                        backgr = 'Not in file'
                        site = 'Not in file'
                    #residue = residue[0].zfill(4)+residue[1]
                    residue = resid
            elif format_ == 'pdb2pka':
                pka = residue[1].atof()
                modelpk = residue[2].atof()
                dpk = residue[3].atof()
                desolv = residue[4].atof()
                backgr = residue[5].atof()
                site = residue[6].atof()
                residue = residue[0]
            #
            # Reformat the residue names if we are asked for the new name
            # structure
            #
            if self.newname:
                residue = reformat_name(residue, nterm, format_)
            #
            # Make sure that non-determined pKa values are marked appropriately
            #
            if pka == 0.0:
                pka = None
            #
            # Construct dictionary
            #
            pKa[residue] = {'pKa':pka, 'modelpK':modelpk, 'desolv':desolv, 'backgr':backgr, 'delec':site}
            linenumber += 1
            if lines[linenumber].lower().strip() == 'End of file'.lower():
                done = 1
        self.pka = pKa
        return self.pka

    #
    # -----
    #

    def write_pka(self, filename, data=None, format_='WHAT IF'):
        """Write a PKA.DAT file containing all info on the calculations"""
        #
        # Get the data
        #
        if not data:
            data = self.pka
        #
        # Write the file
        #
        wfd = open(filename, 'w')
        wfd.write('%s pKa File\n' % format_)
        wfd.write('Format 1.0\n')
        wfd.write('      Group            pKa value  Model pK    dpK     dDesolv    dBack   dElec\n')
        groups = data.keys()
        # Sort accroding to the residue sequence number
        newgroup = {}
        for gname in groups:
            newg = gname.split('_')[2]
            newgroup[int(newg), gname] = gname
        newgroupkeys = sorted(newgroup.keys())
        groups = []
        for idx in newgroupkeys:
            groups.append(idx[1])

        written = {}
        #
        # ---------
        #
        for group in groups:
            if group in data:
                this_data = data[group]
                wfd.write('%15s      %7.4f  %7.4f  %7.4f  %7.4f  %7.4f  %7.4f  \n' %(self.WI_res_text(group, format_),
                                                                                     this_data['pKa'],
                                                                                     this_data['modelpK'],
                                                                                     this_data['pKa']-this_data['modelpK'],
                                                                                     this_data['desolv'],
                                                                                     this_data['backgr'],
                                                                                     this_data['delec']))
                written[group] = 1
        wfd.write('End of file\n')
        wfd.close()
        return

    #
    # -------------------------------
    #

    def read_titration_curve(self, filename=None):
        return self.readtitcurv(filename)

    def readtitcurv(self, filename=None):
        #
        # Syntax: readtitcurv(self, <titration curve filename>)
        # This function reads a WHAT IF titration curve file and
        # creates self.titdata, which is a dictionary:
        # self.titdata = {<residue>:{'pKa':<pka>, <ph1>:<charge1>, <ph2>:<charge2>.....}}
        #
        if not filename:
            filename = self.titcurvfile
        if not os.path.isfile(filename):
            raise 'File does not exist: %s' % filename
        rfd = open(filename)
        lines = rfd.readlines()
        rfd.close()
        #
        # Parse
        #
        if lines[0].strip().lower() == 'WHAT IF Titration Curve File'.lower():
            format_ = 'WHAT IF'
        elif lines[0].strip().lower() == 'pdb2pka Titration Curve File'.lower():
            format_ = 'pdb2pka'
        else:
            raise 'Unknown format'
        if lines[1].strip().lower() != 'Format 1.0'.lower():
            raise 'unknown format: %s' % lines[1]
        phvals = lines[2].split()
        phstart = phvals[0].atof()
        phend = phvals[1].atof()
        phstep = phvals[2].atof()
        titdata = {}
        linenumber = 3
        done = 0
        terms = [':NTERM', ':CTERM']
        term_count = -1
        while not done:
            term = None
            if lines[linenumber].strip() == 'TERMINAL GROUP:':
                linenumber += 1
                term = 1
            residue = getWI_resid2(lines[linenumber], format_)
            if term:
                term_count += 1
                residue = residue+terms[term_count]
                if term_count == 1:
                    term_count = -1
            pKa = float(lines[linenumber].split()[-1])
            linenumber += 1
            #
            # --------------
            #
            charge = {'pKa':pKa}
            for pH in range(int(100 * phstart), int(100 * phend + 100 * phstep), int(100 * phstep)):
                rpH = float(pH) / 100.0
                line = lines[linenumber].split()
                # TODO: 2020/07/04 intendo - isn't this really bad to check a float to another value
                if line[0].atof() == rpH:
                    charge[rpH] = line[1].atof()
                    linenumber += 1
            titdata[residue] = charge
            linenumber += 1
            if lines[linenumber].lower().strip() == 'End of file'.lower():
                done = 1
        self.titdata = titdata
        return self.titdata

    #
    # ----------------------
    #

    def write_titration_curve(self, filename, data, format_='WHAT IF'):
        #
        # This function creates a WHAT IF titration curve file.
        # data is a dictionary:
        # data = {<residue>:{'pKa':<pka>, <ph1>:<charge1>, <ph2>:<charge2>.....}}
        #
        # Extract some data from the dictionary
        #
        residues = data.keys()
        phvals = sorted(data[residues[0]].keys())
        for residue in residues:
            newp_hvals = sorted(data[residue].keys())
            if newp_hvals != phvals:
                _LOGGER.info(phvals)
                _LOGGER.info(newp_hvals)
                raise 'Dictionary does not contain identical pH values'
        #
        # Check that a pKa value is in the pH values
        #
        for residue in residues:
            if 'pKa' not in data[residue]:
                #print 'No pKa value found. Setting to zero!! - Jens change this!!'
                data[residue]['pKa'] = 0.0
        #
        # Find the pH-start, stop and step
        #
        phvals = sorted(data[residues[0]].keys())
        phstart = phvals[0]
        phstop = phvals[-2]
        phstep = phvals[1] - phstart

        wfd = open(filename, 'w')
        #
        # Write header
        #
        wfd.write('%s Titration Curve File\n' % format_)
        wfd.write('Format 1.0\n')
        #
        # Start pH, end pH, pH step
        #
        wfd.write('%6.3f %7.3f %6.3f\n' %(phstart, phstop, phstep))
        residues = data.keys()
        # Sort accroding to the residue sequence number
        newresidue = {}
        for r in residues:
            newr = r.split('_')[2]
            newresidue[int(newr), r] = r
        newresiduekeys = sorted(newresidue.keys())
        residues = []
        for k in newresiduekeys:
            residues.append(k[1])

        for residue in residues:
            wfd.write('%s      %7.4f\n' %(self.WI_res_text(residue, format_), float(data[residue]['pKa'])))
            for ph in phvals:
                if ph == 'pKa':
                    continue
                wfd.write('%.2f  %.3f\n' %(float(ph), float(data[residue][ph])))
            wfd.write('------------------------------------------\n')
        wfd.write('End of file\n')
        #
        # Close file
        #
        wfd.close()
        #
        # This will never work without a template file.
        # It is not worth the trouble to reconstruct WHAT IFs residue identifier line
        #
        return

    #
    # ----------------------------------
    #

    def read_matrix(self, filename=None):
        #
        # This subroutine read a MATRIX file
        #
        if not filename:
            if self.matrix_file:
                filename = self.matrix_file
            else:
                raise 'No matrix filename given'
        #
        if not os.path.isfile(filename):
            raise "File not found: %s" % filename
        rfd = open(filename)
        lines = rfd.readlines()
        rfd.close()
        #
        # Initialise dictionary
        #
        self.matrix = {}
        #
        # Read title lines
        #
        if lines[0].strip().lower() == 'WHAT IF Interaction Matrix File'.lower():
            format_ = 'WHAT IF'
        elif lines[0].strip().lower() == 'pdb2pka Interaction Matrix File.lower()'.lower():
            format_ = 'WHAT IF'
        else:
            raise 'Unknown format'
        if not lines[1].strip() == 'Format 1.0':
            raise 'Wrong format: %s' % lines[1]
        idx = 1
        done = None
        partners = None
        nterm = 0
        while not done:
            idx += 1
            #
            # Read first line for this partner residue
            #
            if format_ == 'WHAT IF':
                term = None
                if lines[idx].strip() == 'TERMINAL GROUP:':
                    term = 1
                    nterm = abs(nterm - 1)
                    idx += 1
                nline = lines[idx].replace('(', '')
                nline = nline.replace(')', '')
                list_ = nline.split()
                if len(list_[3]) == 1:
                    resid = list_[2].zfill(4) + list_[1].upper() + list_[3]
                else:
                    resid = list_[2].zfill(4) + list_[1].upper()
                    chainid = None
                if term:
                    resid = 'T' + resid
                #
                # Should we use the new naming structure?
                #
                if self.newname:
                    resid = reformat_name(resid, nterm, format_)
                #
                #
                #
                np = int(list_[-1].atof())
                if not partners:
                    partners = np
                else:
                    if partners != np:
                        raise 'Number of partners changes: %s' % np
                self.matrix[resid] = {}
                #
                # Now read all the interactions with the partners
                #
                nterm_partner = 0
                for count in range(partners):
                    idx += 1
                    term2 = None
                    if lines[idx].strip() == 'TERMINAL GROUP:':
                        nterm_partner = abs(nterm_partner - 1)
                        term2 = 1
                        idx += 1
                    nline = lines[idx].replace('(', '')
                    nline = nline.replace(')', '')
                    list_ = nline.split()
                    if len(list_[3]) == 1:
                        partid = list_[2].zfill(4) + list_[1].upper() + list_[3]
                    else:
                        partid = list_[2].zfill(4) + list_[1].upper()
                    if term2:
                        partid = 'T' + partid
                    #
                    # New name?
                    #
                    if self.newname:
                        partid = reformat_name(partid, nterm_partner, format_)
                    chacha = list_[-1].strip().atof()
                    idx += 1
                    interaction2 = lines[idx].atof()
                    idx += 1
                    interaction3 = lines[idx].atof()
                    idx += 1
                    interaction4 = lines[idx].atof()
                    energies = [chacha, interaction2, interaction3, interaction4]
                    self.matrix[resid][partid] = energies
                    term2 = None
            elif format_ == 'pdb2pka':
                #
                # pseudo-pdb2pka format
                #
                list_ = lines[idx].split()
                resid = list_[0].strip()
                self.matrix[resid] = {}
                partners = int(float(list_[-1]))
                #
                # Now read all the interactions with the partners
                #
                for count in range(partners):
                    idx += 1
                    list_ = lines[idx].split()
                    partid = list_[0]
                    chacha = list_[-1].strip().atof()
                    idx += 1
                    interaction2 = lines[idx].atof()
                    idx += 1
                    interaction3 = lines[idx].atof()
                    idx += 1
                    interaction4 = lines[idx].atof()
                    energies = [chacha, interaction2, interaction3, interaction4]
                    self.matrix[resid][partid] = energies
            idx += 1
            if lines[idx + 1].strip() == 'End of file':
                done = 1
        return self.matrix

    #
    # -------------------------
    #

    def write_matrix(self, filename, format_='WHAT IF'):
        #
        # Writes an interaction energy matrix
        #
        wfd = open(filename, 'w')
        wfd.write('%s Interaction Matrix File\n' % format_)
        wfd.write('Format 1.0\n')
        groups = sorted(self.matrix.keys())

        num_groups = len(groups)
        #count = 0
        written = {}
        newgroups = []
        for group in groups:
            if group[0] == 'T':
                newgroups.append(group[1:])
            else:
                newgroups.append(group)

        newnewgroup = {}
        for gname in newgroups:
            newg = gname.split('_')[2]
            newnewgroup[int(newg), gname] = gname
        newnewgroupkeys = sorted(newnewgroup.keys())
        newgroups = []
        for k in newnewgroupkeys:
            newgroups.append(k[1])

        self.newgroups = newgroups[:]
        #
        # ---------
        #
        for group in newgroups:
            group_name = 'T' + group
            hk0 = group in self.matrix
            hk1 = group_name in self.matrix
            hk2 = group_name in self.matrix and group_name not in written
            if hk0:
                wfd.write('%s      %7.4f\n' %(self.WI_res_text(group, format_), float(num_groups)))
                self.write_section(group, wfd, format_)
                written[group] = 1
                #
                # Is there a terminal group associated with this residue?
                #
                #if self.matrix.has_key(group_name):
                if hk1:
                    wfd.write('%s      %7.4f\n' % self.WI_res_text(group_name, format_), float(num_groups))
                    self.write_section(group_name, wfd, format_)
                    written[group_name] = 1
            else:
                #if self.matrix.has_key(group_name) and not written.has_key(group_name):
                if hk2:
                    wfd.write('%s      %7.4f\n' %(self.WI_res_text(group_name, format_), float(num_groups)))
                    self.write_section(group_name, wfd, format_)
                    written[group_name] = 1
        wfd.write('End of file\n')
        wfd.close()
        return

    #
    # -----
    #

    def write_pdb2pka_matrix(self, filename, matrix):
        """Write an interaction energy matrix in pdb2pka format
        At the moment, we just reformat and write a WHAT IF file"""
        self.matrix = {}
        for group1 in matrix.keys():
            self.matrix[group1.uniqueid] = {}
            for tit1 in matrix[group1].keys():
                for state1 in matrix[group1][tit1].keys():
                    sub_m = matrix[group1][tit1][state1]
                    for group2 in sub_m.keys():
                        if not group2.uniqueid in self.matrix[group1.uniqueid]:
                            self.matrix[group1.uniqueid][group2.uniqueid] = []
                        for tit2 in sub_m[group2].keys():
                            for state2 in sub_m[group2][tit2].keys():
                                self.matrix[group1.uniqueid][group2.uniqueid].append(sub_m[group2][tit2][state2])
        for group1 in self.matrix:
            for group2 in self.matrix[group1]:
                sum_ = 0.0
                for val in self.matrix[group1][group2]:
                    sum_ += val
                self.matrix[group1][group2] = [sum_, 0.0, 0.0, 0.0]
        self.write_matrix(filename, format_='pdb2pka')
        return

    #
    # ------------------------
    #

    def write_section(self, group, fd, format_):
        groups_tmp = self.matrix[group].keys()
        groups2 = []
        for group_x in groups_tmp:
            if group_x[0] == 'T':
                groups2.append(group_x[1:])
            else:
                groups2.append(group_x)

        # Sort accroding to the residue sequence number
        newgroup = {}
        for gname in groups2:
            newg = gname.split('_')[2]
            newgroup[int(newg), gname] = gname
        newgroupkeys = sorted(newgroup.keys())
        groups2 = []
        for k in newgroupkeys:
            groups2.append(k[1])

        written = {}
        for group2 in groups2:
            group2_name = 'T' + group2
            hk0 = group2 in self.matrix[group]
            hk1 = group2_name in self.matrix[group]
            hk2 = group2_name in self.matrix[group] and group2_name not in written
            if hk0:
                fd.write('%s      %7.4f\n' %(self.WI_res_text(group2, format_), self.matrix[group][group2][0]))
                fd.write('%7.4f\n%7.4f\n%7.4f\n'%(self.matrix[group][group2][1], self.matrix[group][group2][2], self.matrix[group][group2][3]))
                written[group2] = 1
                #
                # Is there a terminal group associated with this residue?
                #
                #if self.matrix[group].has_key(group2_name):
                if hk1:
                    fd.write('%s      %7.4f\n' %(self.WI_res_text(group2_name, format_), self.matrix[group][group2_name][0]))
                    fd.write('%7.4f\n%7.4f\n%7.4f\n'%(self.matrix[group][group2_name][1], self.matrix[group][group2_name][2], self.matrix[group][group2_name][3]))
                    written[group2_name] = 1
            else:
                #if self.matrix[group].has_key(group2_name) and not written.has_key(group2_name):
                if hk2:
                    fd.write('%s      %7.4f\n' %(self.WI_res_text(group2_name, format_), self.matrix[group][group2_name][0]))
                    fd.write('%7.4f\n%7.4f\n%7.4f\n'%(self.matrix[group][group2_name][1], self.matrix[group][group2_name][2], self.matrix[group][group2_name][3]))
                    written[group2_name] = 1
        fd.write('--------------------------------------------\n')
        return

    #
    # ------------------------------
    #

    def read_desolv(self, filename=None):
        if not filename:
            if self.desolv_file:
                filename = self.desolv_file
            else:
                raise 'No desolv filename given'
        #
        #
        # This subroutine reads a DESOLV file
        #
        if not os.path.isfile(filename):
            raise "File not found: %s" % filename
        rfd = open(filename)
        lines = rfd.readlines()
        rfd.close()
        #
        # Initialise dictionary
        #
        self.desolv = {}
        #
        # Read title lines
        #
        if lines[0].strip() == 'WHAT IF Desolvation Energy File' and lines[1].strip() == 'Format 1.0':
            format_ = 'WHAT IF'
        elif lines[0].strip() == 'pdb2pka Desolvation Energy File':
            format_ = 'pdb2pka'
        else:
            raise Exception("Unknown format: %s" % lines[0].strip())
        #
        # Call the generic read routine
        #
        self.read_WIfile(lines, self.desolv, format_)
        return self.desolv

    #
    # -----------------------------
    #

    def read_backgr(self, filename=None):
        #
        # This subroutine reads a BACKGR file
        #
        if not filename:
            if self.backgr_file:
                filename = self.backgr_file
            else:
                raise 'No matrix filename given'
        #
        if not os.path.isfile(filename):
            raise "File not found: %s" % filename
        rfd = open(filename)
        lines = rfd.readlines()
        rfd.close()
        #
        # Initialise dictionary
        #
        self.backgr = {}
        #
        # Read title lines
        #
        if lines[0].strip() == 'WHAT IF Background Energy File':
            format_ = 'WHAT IF'
        elif lines[0].strip() == 'pdb2pka Background Energy File':
            format_ = 'pdb2pka'
        else:
            raise Exception('Unknown format: %s' % lines[0].strip())
        #
        # Call the generic read routine
        #
        self.read_WIfile(lines, self.backgr, format_)
        return self.backgr

    #
    # ----------------------------------
    #


    def read_WIfile(self, lines, dict_, format_):
        #
        # Read a DESOLV file or a BACKGR file
        #
        idx = 1
        done = None
        nterm = 0
        while not done:
            idx += 1
            #
            # Read first line for this residue
            #
            term = None
            if lines[idx].strip() == 'TERMINAL GROUP:':
                nterm = abs(nterm - 1)
                term = 1
                idx += 1
            nline = lines[idx].replace('(', '')
            nline = nline.replace(')', '')
            list_ = nline.strip()
            if len(list_[3]) == 1:
                resid = list_[2].zfill(4) + list_[1].upper() + list_[3]
            else:
                resid = list_[2].zfill(4) + list_[1].upper()
                chainid = None
            if term:
                resid = 'T' + resid
            #
            # New name?
            #
            if self.newname:
                resid = reformat_name(resid, nterm)
            #
            dict_[resid] = list_[-1].atof()
            if lines[idx + 1].strip() == 'End of file':
                done = 1
        return dict_

    #
    # ----------------------
    #

    def write_desolv(self, filename, format_='WHAT IF'):
        #
        # Writes the desolvation file
        #
        wfd = open(filename, 'w')
        wfd.write('%s Desolvation Energy File\n' % format_)
        wfd.write('Format 1.0\n')
        groups = self.desolv.keys()
        # Sort accroding to the residue sequence number
        newgroup = {}
        for g in groups:
            newg = g.split('_')[2]
            newgroup[int(newg), g] = g
        newgroupkeys = sorted(newgroup.keys())
        groups = []
        for k in newgroupkeys:
            groups.append(k[1])
        written = {}
        #
        # ---------
        #
        for group in groups:
            if group in self.desolv:
                wfd.write('%s      %7.4f\n' %(self.WI_res_text(group, format_), float(self.desolv[group])))
                written[group] = 1
        wfd.write('End of file\n')
        wfd.close()
        return

    #
    # ----------------------
    #

    def write_backgr(self, filename, format_='WHAT IF'):
        #
        # Writes the background interaction energy file
        #
        wfd = open(filename, 'w')
        wfd.write('%s Background Energy File\n' % format_)
        wfd.write('Format 1.0\n')
        groups = self.backgr.keys()
        # Sort accroding to the residue sequence number
        newgroup = {}
        for gname in groups:
            newg = gname.split('_')[2]
            newgroup[int(newg), gname] = gname
        newgroupkeys = sorted(newgroup.keys())
        groups = []
        for idx in newgroupkeys:
            groups.append(idx[1])
        written = {}
        #
        # ---------
        #
        for group in groups:
            if group in self.backgr:
                wfd.write('%s      %7.4f\n' %(self.WI_res_text(group, format_), float(self.backgr[group])))
                written[group] = 1
        wfd.write('End of file\n')
        wfd.close()
        return

    #
    # ----------------------
    #

    def WI_res_text(self, residue, format_):
        """Constructs the WHAT IF residue ID line
        f.ex. 1 LYS  (   1  ) from 0001LYS.
        Function works with new names."""
        if format_ == 'WHAT IF':
            if not self.newname:
                # Old names
                terminal = None
                if residue[0] == "T":
                    terminal = 1
                    residue = residue[1:]
                number = residue[:4].atoi()
                residue = residue[4:]
                if len(residue) > 3:
                    chainid = residue[-1]
                    residue = residue[:-1]
                else:
                    chainid = ' '
                line = '%4d %3s  (%4d  ) %1s' %(number, residue, number, chainid)
                if terminal:
                    line = 'TERMINAL GROUP:\n'+line
                return line
            else:
                #
                # New names
                #
                #print 'In WI_res_text', residue, format
                terminal = None
                split = residue.split(':')
                if split[-1] == "CTERM" or split[-1] == 'NTERM':
                    terminal = 1
                try:
                    number = int(split[1])
                    residue = split[2]
                    chainid = split[0]
                    line = '%4d %3s  (%4d  ) %1s' %(number, residue, number, chainid)
                    if terminal:
                        line = 'TERMINAL GROUP:\n'+line
                    return line
                except:
                    return residue
        elif format_ == 'pdb2pka':
            #
            # PDB2PKA format
            #
            terminal = None
            split = residue.split(':')
            if split[1] == 'NTR' or split[1] == 'CTR':
                terminal = 1
            #
            res = split[0]
            res = res.split('_')
            residue = res[0]
            chainid = res[1]
            #
            # For Design_pKa
            #
            #chainid = ''
            #
            number = int(res[2])
            line = '%4d %3s  (%4d  ) %1s' %(number, residue, number, chainid)
            if terminal:
                line = 'TERMINAL GROUP:\n'+line
            return line
        else:
            raise Exception('Unknown format:' + format_)
