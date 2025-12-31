import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Badge,
  Box,
  Button,
  ButtonProps,
  chakra,
  Checkbox,
  FormControl,
  FormLabel,
  HStack,
  IconButton,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Text,
  Tooltip,
  useToast,
  VStack,
} from "@chakra-ui/react";
import {
  PlusIcon as HeroIconPlusIcon,
  UserGroupIcon,
} from "@heroicons/react/24/outline";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  FetchAdminsQueryKey,
  getAdminDefaultValues,
  AdminSchema,
  AdminType,
  useAdmins,
  useAdminsQuery,
} from "contexts/AdminsContext";
import { FC, ReactNode, useState } from "react";
import { Controller, useForm, UseFormReturn } from "react-hook-form";
import { useTranslation } from "react-i18next";
import {
  UseMutateFunction,
  useMutation,
  useQueryClient,
} from "react-query";
import { formatBytes } from "utils/formatByte";
import {
  generateErrorMessage,
  generateSuccessMessage,
} from "utils/toastHandler";
import { useDashboard } from "../contexts/DashboardContext";
import { DeleteAdminModal } from "./DeleteAdminModal";
import { DeleteIcon } from "./DeleteUserModal";
import { Icon } from "./Icon";

import { Input } from "./Input";

const CustomInput = chakra(Input, {
  baseStyle: {
    bg: "white",
    _dark: {
      bg: "gray.700",
    },
  },
});

const ModalIcon = chakra(UserGroupIcon, {
  baseStyle: {
    w: 5,
    h: 5,
  },
});

const PlusIcon = chakra(HeroIconPlusIcon, {
  baseStyle: {
    w: 5,
    h: 5,
    strokeWidth: 2,
  },
});

type AccordionAdminType = {
  toggleAccordion: () => void;
  admin: AdminType;
};

const AdminAccordion: FC<AccordionAdminType> = ({ toggleAccordion, admin }) => {
  const { updateAdmin, setDeletingAdmin } = useAdmins();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const toast = useToast();
  const form = useForm<AdminType>({
    defaultValues: admin,
    resolver: zodResolver(AdminSchema),
  });
  const handleDeleteAdmin = setDeletingAdmin.bind(null, admin);

  const { isLoading, mutate } = useMutation(updateAdmin, {
    onSuccess: () => {
      generateSuccessMessage("Admin updated successfully", toast);
      queryClient.invalidateQueries(FetchAdminsQueryKey);
    },
    onError: (e) => {
      generateErrorMessage(e, toast, form);
    },
  });

  return (
    <AccordionItem
      border="1px solid"
      _dark={{ borderColor: "gray.600" }}
      _light={{ borderColor: "gray.200" }}
      borderRadius="4px"
      p={1}
      w="full"
    >
      <AccordionButton px={2} borderRadius="3px" onClick={toggleAccordion}>
        <HStack w="full" justifyContent="space-between" pr={2}>
          <HStack flex="1" spacing={2}>
            <Text
              as="span"
              fontWeight="medium"
              fontSize="sm"
              textAlign="left"
              color="gray.700"
              _dark={{ color: "gray.300" }}
            >
              {admin.username}
            </Text>
            {admin.users_usage !== null && admin.users_usage !== undefined && (
              <Text
                as="span"
                fontSize="xs"
                color="gray.500"
                _dark={{ color: "gray.500" }}
              >
                ({formatBytes(admin.users_usage)})
              </Text>
            )}
          </HStack>
          <HStack>
            {admin.is_sudo && (
              <Badge
                colorScheme="purple"
                rounded="full"
                display="inline-flex"
                px={3}
                py={1}
              >
                <Text
                  textTransform="capitalize"
                  fontSize="0.7rem"
                  fontWeight="medium"
                  letterSpacing="tighter"
                >
                  Sudo
                </Text>
              </Badge>
            )}
          </HStack>
        </HStack>
        <AccordionIcon />
      </AccordionButton>
      <AccordionPanel px={2} pb={2}>
        <AdminForm
          form={form}
          mutate={mutate}
          isLoading={isLoading}
          submitBtnText={t("admins.editAdmin", "Edit Admin")}
          btnLeftAdornment={
            <Tooltip label={t("delete")} placement="top">
              <IconButton
                colorScheme="red"
                variant="ghost"
                size="sm"
                aria-label="delete admin"
                onClick={handleDeleteAdmin}
              >
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          }
          isEditing
        />
      </AccordionPanel>
    </AccordionItem>
  );
};

type AddAdminFormType = {
  toggleAccordion: () => void;
  resetAccordions: () => void;
};

const AddAdminForm: FC<AddAdminFormType> = ({
  toggleAccordion,
  resetAccordions,
}) => {
  const toast = useToast();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { addAdmin } = useAdmins();
  const form = useForm<AdminType>({
    resolver: zodResolver(AdminSchema),
    defaultValues: getAdminDefaultValues(),
  });
  const { isLoading, mutate } = useMutation(addAdmin, {
    onSuccess: () => {
      generateSuccessMessage(
        t("admins.addAdminSuccess", { username: form.getValues("username") }),
        toast
      );
      queryClient.invalidateQueries(FetchAdminsQueryKey);
      form.reset();
      resetAccordions();
    },
    onError: (e) => {
      generateErrorMessage(e, toast, form);
    },
  });
  return (
    <AccordionItem
      border="1px solid"
      _dark={{ borderColor: "gray.600" }}
      _light={{ borderColor: "gray.200" }}
      borderRadius="4px"
      p={1}
      w="full"
    >
      <AccordionButton px={2} borderRadius="3px" onClick={toggleAccordion}>
        <Text
          as="span"
          fontWeight="medium"
          fontSize="sm"
          flex="1"
          textAlign="left"
          color="gray.700"
          _dark={{ color: "gray.300" }}
          display="flex"
          gap={1}
        >
          <PlusIcon display={"inline-block"} />{" "}
          <span>{t("admins.addNewAdmin", "Add New Admin")}</span>
        </Text>
      </AccordionButton>
      <AccordionPanel px={2} py={4}>
        <AdminForm
          form={form}
          mutate={mutate}
          isLoading={isLoading}
          submitBtnText={t("admins.addAdmin", "Add Admin")}
          btnProps={{ variant: "solid" }}
        />
      </AccordionPanel>
    </AccordionItem>
  );
};

type AdminFormType = FC<{
  form: UseFormReturn<AdminType>;
  mutate: UseMutateFunction<unknown, unknown, any>;
  isLoading: boolean;
  submitBtnText: string;
  btnProps?: Partial<ButtonProps>;
  btnLeftAdornment?: ReactNode;
  isEditing?: boolean;
}>;

const AdminForm: AdminFormType = ({
  form,
  mutate,
  isLoading,
  submitBtnText,
  btnProps = {},
  btnLeftAdornment,
  isEditing = false,
}) => {
  const { t } = useTranslation();

  return (
    <form onSubmit={form.handleSubmit((v) => mutate(v))}>
      <VStack>
        <HStack w="full">
          <FormControl>
            <CustomInput
              label={t("admins.username", "Username")}
              size="sm"
              placeholder="admin"
              {...form.register("username")}
              error={form.formState?.errors?.username?.message}
              disabled={isEditing}
            />
          </FormControl>
        </HStack>
        <HStack w="full">
          <FormControl>
            <CustomInput
              label={t("admins.password", "Password")}
              size="sm"
              type="password"
              placeholder={isEditing ? "Leave empty to keep current" : "••••••••"}
              {...form.register("password")}
              error={form.formState?.errors?.password?.message}
            />
          </FormControl>
        </HStack>
        <HStack alignItems="flex-start" w="100%">
          <Box w="100%">
            <CustomInput
              label={t("admins.telegramId", "Telegram ID")}
              size="sm"
              placeholder="123456789"
              {...form.register("telegram_id")}
              error={form.formState?.errors?.telegram_id?.message}
            />
          </Box>
        </HStack>
        <HStack alignItems="flex-start" w="100%">
          <Box w="100%">
            <CustomInput
              label={t("admins.discordWebhook", "Discord Webhook")}
              size="sm"
              placeholder="https://discord.com/api/webhooks/..."
              {...form.register("discord_webhook")}
              error={form.formState?.errors?.discord_webhook?.message}
            />
          </Box>
        </HStack>
        <HStack alignItems="flex-start" w="100%">
          <Box w="100%">
            <CustomInput
              label={t("admins.subscriptionTitle", "Subscription Title")}
              size="sm"
              placeholder="My VPN Service"
              {...form.register("subscription_title")}
              error={form.formState?.errors?.subscription_title?.message}
            />
          </Box>
        </HStack>
        <HStack alignItems="flex-start" w="100%">
          <Box w="100%">
            <CustomInput
              label={t("admins.announce", "Announce Text")}
              size="sm"
              placeholder="Welcome to VPN! Username: {username}"
              {...form.register("announce")}
              error={form.formState?.errors?.announce?.message}
            />
          </Box>
        </HStack>
        <HStack alignItems="flex-start" w="100%">
          <Box w="100%">
            <CustomInput
              label={t("admins.announceUrl", "Announce URL")}
              size="sm"
              placeholder="https://t.me/support_channel"
              {...form.register("announce_url")}
              error={form.formState?.errors?.announce_url?.message}
            />
          </Box>
        </HStack>
        <FormControl py={1}>
          <Controller
            name="is_sudo"
            control={form.control}
            render={({ field }) => (
              <Checkbox
                isChecked={field.value}
                onChange={(e) => field.onChange(e.target.checked)}
              >
                <FormLabel m={0}>
                  {t("admins.isSudo", "Sudo Admin")}
                </FormLabel>
              </Checkbox>
            )}
          />
        </FormControl>
        <HStack w="full">
          {btnLeftAdornment}
          <Button
            flexGrow={1}
            type="submit"
            colorScheme="primary"
            size="sm"
            px={5}
            w="full"
            isLoading={isLoading}
            {...btnProps}
          >
            {submitBtnText}
          </Button>
        </HStack>
      </VStack>
    </form>
  );
};

export const AdminsDialog: FC = () => {
  const { isEditingAdmins, onEditingAdmins } = useDashboard();
  const { t } = useTranslation();
  const [openAccordions, setOpenAccordions] = useState<any>({});
  const { data: admins, isLoading } = useAdminsQuery();

  const onClose = () => {
    setOpenAccordions({});
    onEditingAdmins(false);
  };

  const toggleAccordion = (index: number | string) => {
    if (openAccordions[String(index)]) {
      delete openAccordions[String(index)];
    } else openAccordions[String(index)] = {};

    setOpenAccordions({ ...openAccordions });
  };

  return (
    <>
      <Modal isOpen={isEditingAdmins} onClose={onClose}>
        <ModalOverlay bg="blackAlpha.300" backdropFilter="blur(10px)" />
        <ModalContent mx="3" w="fit-content" maxW="3xl">
          <ModalHeader pt={6}>
            <Icon color="primary">
              <ModalIcon color="white" />
            </Icon>
          </ModalHeader>
          <ModalCloseButton mt={3} />
          <ModalBody w="440px" pb={6} pt={3}>
            <Text mb={3} opacity={0.8} fontSize="sm">
              {t("admins.title", "Admins Management")}
            </Text>
            {isLoading && "loading..."}

            <Accordion
              w="full"
              allowToggle
              index={Object.keys(openAccordions).map((i) => parseInt(i))}
            >
              <VStack w="full">
                {!isLoading &&
                  admins &&
                  admins.map((admin, index) => {
                    return (
                      <AdminAccordion
                        toggleAccordion={() => toggleAccordion(index)}
                        key={admin.username}
                        admin={admin}
                      />
                    );
                  })}

                <AddAdminForm
                  toggleAccordion={() => toggleAccordion((admins || []).length)}
                  resetAccordions={() => setOpenAccordions({})}
                />
              </VStack>
            </Accordion>
          </ModalBody>
        </ModalContent>
      </Modal>
      <DeleteAdminModal deleteCallback={() => setOpenAccordions({})} />
    </>
  );
};
